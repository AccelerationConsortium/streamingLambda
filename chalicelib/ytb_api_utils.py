import boto3
import pickle
import time
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/youtube"]
CHANNEL_ID = "UCHBzCfYpGwoqygH9YNh9A6g"

YOUTUBE = None
S3_BUCKET = "ac-token-youtube-api"
S3_KEY = "token/token.pickle"

def init_youtube_service():
    global YOUTUBE
    if YOUTUBE is None:
        creds = None
        local_path = "/tmp/token.pickle"

        # Download token from S3
        s3 = boto3.client("s3")
        s3.download_file(S3_BUCKET, S3_KEY, local_path)

        with open(local_path, "rb") as token_file:
            creds = pickle.load(token_file)

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(local_path, "wb") as token_file:
                pickle.dump(creds, token_file)

            s3.upload_file(local_path, S3_BUCKET, S3_KEY)

        if not creds or not creds.valid:
            raise RuntimeError("No valid credentials available.")

        YOUTUBE = build("youtube", "v3", credentials=creds)

def get_own_channel_id():
    channels = YOUTUBE.channels().list(part="id", mine=True).execute()
    return channels["items"][0]["id"]


def list_broadcasts(broadcast_status="active", max_results=50):
    broadcasts_list = YOUTUBE.liveBroadcasts().list(
        part="id,snippet,status",
        broadcastStatus=broadcast_status,
        maxResults=max_results
    ).execute()
    return broadcasts_list.get("items", [])

def end_active_broadcasts_for_device(workflow_name: str):
    broadcasts_list = list_broadcasts("active")

    for broadcast in broadcasts_list:
        title = broadcast["snippet"]["title"]
        life_cycle_status = broadcast["status"]["lifeCycleStatus"]
        if workflow_name.lower() in title.lower() and life_cycle_status in ("live", "testing"):
            broadcast_id = broadcast["id"]
            print(f"Ending broadcast: {broadcast_id} | Title: {title} | Status: {life_cycle_status}")
            YOUTUBE.liveBroadcasts().transition(
                broadcastStatus="complete",
                id=broadcast_id,
                part="status"
            ).execute()

def create_broadcast_and_bind_stream(cam_name: str,workflow_name: str, privacy_status: str):

    if privacy_status not in ("public", "private", "unlisted"):
        raise ValueError(f"Invalid privacy status: {privacy_status}")

    print(f"Creating new stream id for '{workflow_name}'")
    stream_response = YOUTUBE.liveStreams().insert(
          part="snippet,cdn,contentDetails",
                body={
                    "snippet": {"title": f"{workflow_name} stream key"},
                    "cdn": {
                        "frameRate": "variable",
                        "resolution": "variable",
                        "ingestionType": "rtmp"
                    },
                    "contentDetails": {
                        "isReusable": False 
                    }
                }
            ).execute()

    stream_id = stream_response["id"]
    ingestion_info = stream_response["cdn"]["ingestionInfo"]
    stream_url = ingestion_info["ingestionAddress"]
    stream_key = ingestion_info["streamName"]
    ffmpeg_url = f"{stream_url}/{stream_key}"



    # Set broadcast to start two mins later
    start_time = (datetime.utcnow() + timedelta(minutes=2)).isoformat("T") + "Z"
    formatted_time = datetime.utcnow().strftime("%Y-%m-%d UTC %H:%M")
    broadcast_title = f"{workflow_name} stream {cam_name}, {formatted_time}"
    broadcast_description = (
        f"Live camera feed from {workflow_name} stationed in Toronto, ON "
        "at the Acceleration Consortium (AC).\n\n"
        "https://acceleration.utoronto.ca/"
    )

    broadcast_response = YOUTUBE.liveBroadcasts().insert(
        part="snippet,contentDetails,status",
        body={
            "snippet": {
                "title": broadcast_title,
                "description": broadcast_description,
                "scheduledStartTime": start_time,
                "categoryId": 28
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False
            },
            "contentDetails": {
                "enableAutoStart": True,
                "enableAutoStop": False,
                "latencyPreference": "Low",
                "monitorStream": {
                    "enableMonitorStream": False
                }
            }
        }
    ).execute()

    broadcast_id = broadcast_response["id"]
    video_id = broadcast_id

    playlist_add_status = "unknown"

    # Bind stream to broadcast
    YOUTUBE.liveBroadcasts().bind(
        part="id,contentDetails",
        id=broadcast_id,
        streamId=stream_id
    ).execute()

    # Sleep to let YouTube register the video
    time.sleep(5)

    # Check if playlist exists
    playlists = YOUTUBE.playlists().list(
        part="id,snippet",
        mine=True,
        maxResults=50
    ).execute()

    playlist_id = None
    for p in playlists["items"]:
        if workflow_name.lower() in p["snippet"]["title"].lower():
            playlist_id = p["id"]
            break

    if not playlist_id:
        playlist_response = YOUTUBE.playlists().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": f"{workflow_name} Livestreams Playlist",
                    "description": f"Livestreams for device {workflow_name}"
                },
                "status": {
                    "privacyStatus": privacy_status
                }
            }
        ).execute()
        playlist_id = playlist_response["id"]

    # Attempt to add to playlist
    try:
        YOUTUBE.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": video_id
                    }
                }
            }
        ).execute()
        playlist_add_status = "added"
        print(f"[✓] Broadcast {video_id} successfully added to playlist {playlist_id}.")
    except Exception as e:
        playlist_add_status = f"failed - {e}"
        print(f"[⚠] Failed to add broadcast {video_id} to playlist {playlist_id}: {e}")


    return {
        "broadcast_id": broadcast_id,
        "video_id": video_id,
        "stream_id": stream_id,
        "playlist_id": playlist_id,
        "title": broadcast_title,
        "privacy_status": privacy_status,
        "ffmpeg_url": ffmpeg_url,
        "video_url": f"https://www.youtube.com/watch?v={video_id}",
        "playlist_add_status": playlist_add_status
    }
