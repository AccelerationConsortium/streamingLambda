import json
import logging
from chalice import Chalice
from chalicelib.ytb_api_utils import (
    init_youtube_service,
    create_broadcast_and_bind_stream,
    end_active_broadcasts_for_device
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

app = Chalice(app_name="youtube-stream")

@app.lambda_function()
def lambda_handler(event, context):
    logger.info("Lambda handler invoked")
    try:
        body = event.get("body")
        if isinstance(body, str):
            payload = json.loads(body)
        elif isinstance(body, dict):
            payload = body
        else:
            raise ValueError("Invalid body format")

        logger.info(f"Received payload: {payload}")

        action = payload.get("action")
        cam_name = payload.get("cam_name", "UnknownCam")
        workflow_name = payload.get("workflow_name", "UnknownWorkflow")
        privacy_status = payload.get("privacy_status", "private")

        if action not in ("create", "end"):
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Invalid or missing 'action'. Must be 'create' or 'end'."})
            }

        init_youtube_service()

        if action == "create":
            result = create_broadcast_and_bind_stream(cam_name, workflow_name, privacy_status)
            return {
                "statusCode": 200,
                "body": json.dumps({"status": "created", "result": result})
            }
        else:  # action == "end"
            ended = end_active_broadcasts_for_device(workflow_name)
            return {
                "statusCode": 200,
                "body": json.dumps({"status": "ended", "message": f"{workflow_name} ended successfully"})
            }

    except Exception as e:
        logger.exception("Error in lambda_handler")
        return {
            "statusCode": 400,
            "body": json.dumps({"error": f"Invalid JSON or internal error: {str(e)}"})
        }