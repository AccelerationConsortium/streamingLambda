import json
import logging
from chalicelib.ytb_api_utils import (
    init_youtube_service,
    create_broadcast_and_bind_stream,
    end_active_broadcasts_for_device
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    AWS Lambda handler function for YouTube streaming management.
    
    This function can be directly deployed to AWS Lambda without Chalice.
    
    Expected event payload:
    {
        "body": {
            "action": "create" or "end",
            "cam_name": "camera name",
            "workflow_name": "workflow identifier",
            "privacy_status": "public", "private", or "unlisted" (optional, default: "private")
        }
    }
    """
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
            end_active_broadcasts_for_device(workflow_name)
            return {
                "statusCode": 200,
                "body": json.dumps({"status": "ended", "message": f"{workflow_name} ended successfully"})
            }

    except ValueError as ve:
        logger.exception("Invalid input")
        return {
            "statusCode": 400,
            "body": json.dumps({"error": f"Invalid input: {str(ve)}"})
        }
    except Exception as e:
        logger.exception("Error in lambda_handler")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"Internal server error: {str(e)}"})
        }
