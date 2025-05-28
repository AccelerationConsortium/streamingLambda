import json
from ytb_api_utils import (
    init_youtube_service,
    create_broadcast_and_bind_stream,
    end_active_broadcasts_for_device
)

import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info("Handler invoked")

    #Unwrap the payload
    try:
        # If API Gateway / Function URL wrapped it, it'll be a JSON string under "body"
        raw = event.get("body", "")
        payload = json.loads(raw) if isinstance(raw, str) else raw
    except json.JSONDecodeError:
        # Fallback: assume the event itself is the payload
        payload = event

    #Extract parameters
    action = payload.get("action")
    cam_name = payload.get("cam_name", "UnknownCam")
    workflow_name = payload.get("workflow_name", "UnknownWorkflow")
    privacy_status = payload.get("privacy_status", "private") # "private", "unlisted"


    if action not in ("create", "end"):
        return {
            "statusCode": 400,
            "body": "Invalid or missing 'action'. Must be 'create' or 'end'."
        }

    try:
        init_youtube_service()

        if action == "create":
            result = create_broadcast_and_bind_stream(cam_name,workflow_name, privacy_status)
            return {
                "statusCode": 200,
                "body": result
            }

        else:  # action == "end"
            ended = end_active_broadcasts_for_device(workflow_name)
            return {
                "statusCode": 200,
                "body": f"{workflow_name} ended successfully"
            }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": f"Error during '{action}' for device '{workflow_name}': {str(e)}"
        }