# YouTube Streaming Lambda Function

This repository provides an AWS Lambda function for automatic YouTube livestream creation and management from [monitoring devices](https://ac-training-lab.readthedocs.io/en/latest/devices/picam.html).

## Deployment Options

### Option 1: Direct AWS Lambda Deployment (Recommended for external users)

This method allows you to deploy the Lambda function directly to AWS without requiring Chalice or any special deployment tools. Perfect for users outside the Acceleration Consortium who want to set up their own YouTube streaming Lambda function.

#### Prerequisites

1. AWS Account with Lambda access
2. YouTube Data API v3 credentials
3. S3 bucket for storing YouTube API token (token.pickle)

#### Steps

1. **Download the deployment package**
   
   Go to the [Releases](../../releases) page and download the latest `deployment.zip` file.
   
   Alternatively, build it yourself:
   ```bash
   # Clone the repository
   git clone https://github.com/AccelerationConsortium/streamingLambda.git
   cd streamingLambda
   
   # Create dependencies directory
   mkdir dependencies
   
   # Install dependencies
   pip install --target ./dependencies \
     boto3 \
     google-api-python-client \
     google-auth \
     google-auth-oauthlib \
     google-auth-httplib2
   
   # Copy lambda function and chalicelib
   cp lambda_function.py dependencies/
   cp -r chalicelib dependencies/
   
   # Create deployment package
   cd dependencies
   zip -r ../deployment.zip .
   cd ..
   ```

2. **Upload to AWS Lambda**
   
   - Log in to the [AWS Lambda Console](https://console.aws.amazon.com/lambda)
   - Click "Create function"
   - Choose "Author from scratch"
   - Function name: `youtube-stream` (or your preferred name)
   - Runtime: Python 3.11
   - Click "Create function"
   - In the "Code" section, click "Upload from" → ".zip file"
   - Upload your `deployment.zip` file
   - Click "Save"

3. **Configure the Lambda function**
   
   - **Memory**: Set to at least 512 MB (recommended: 1024 MB)
   - **Timeout**: Set to at least 30 seconds (recommended: 60 seconds)
   - **IAM Role**: Ensure the Lambda execution role has permissions to:
     - Read/write to your S3 bucket (for token.pickle)
     - CloudWatch Logs (for logging)

4. **Set up S3 bucket for YouTube token**
   
   - Create an S3 bucket (e.g., `my-youtube-token-bucket`)
   - Upload your `token.pickle` file to `token/token.pickle` in the bucket
   - Update the S3 bucket name in `chalicelib/ytb_api_utils.py` (lines 12-13):
     ```python
     S3_BUCKET = "your-bucket-name"
     S3_KEY = "token/token.pickle"
     ```
     Then rebuild and redeploy the zip file.

5. **Create a Function URL (optional but recommended)**
   
   - In the Lambda function configuration, go to "Configuration" → "Function URL"
   - Click "Create function URL"
   - Auth type: Choose "AWS_IAM" or "NONE" based on your security requirements
   - Click "Save"
   - Copy the Function URL for use with your monitoring device

6. **Test the function**
   
   Use the Test tab in AWS Lambda Console with this test event:
   ```json
   {
     "body": {
       "action": "create",
       "cam_name": "TestCamera",
       "workflow_name": "TestWorkflow",
       "privacy_status": "private"
     }
   }
   ```

#### API Usage

The Lambda function accepts POST requests with the following payload:

```json
{
  "body": {
    "action": "create",
    "cam_name": "Camera1",
    "workflow_name": "MyWorkflow",
    "privacy_status": "private"
  }
}
```

- `action`: Either "create" (to start a stream) or "end" (to end active streams)
- `cam_name`: Name of your camera/device
- `workflow_name`: Identifier for your workflow (used to group streams)
- `privacy_status`: "public", "private", or "unlisted" (default: "private")

### Option 2: Deployment via Chalice (For AC organization)

This method uses [AWS Chalice](https://github.com/aws/chalice) for automatic deployment and is primarily used by the Acceleration Consortium for internal deployments.

#### Prerequisites

- AWS credentials configured
- Python 3.11+
- Chalice installed

#### Steps

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Deploy to AWS:
   ```bash
   chalice deploy --stage dev
   ```

## How It Works

The Lambda function integrates with the YouTube Data API v3 to:

1. **Create broadcasts**: Automatically creates a YouTube live broadcast with a stream key
2. **Manage streams**: Binds streams to broadcasts and configures settings
3. **End broadcasts**: Gracefully ends active broadcasts for a given workflow
4. **Organize content**: Adds broadcasts to workflow-specific playlists

## Configuration

### YouTube API Credentials

The function requires a `token.pickle` file containing valid YouTube API credentials stored in an S3 bucket. This token is automatically refreshed when expired.

### Environment Variables

If you need to customize the S3 bucket or channel ID, modify the constants in `chalicelib/ytb_api_utils.py`:

```python
CHANNEL_ID = "your-channel-id"
S3_BUCKET = "your-bucket-name"
S3_KEY = "token/token.pickle"
```

## Related Documentation

- [AC Training Lab - PiCam Device Setup](https://ac-training-lab.readthedocs.io/en/latest/devices/picam.html)
- [AWS Lambda Python Package Documentation](https://docs.aws.amazon.com/lambda/latest/dg/python-package.html)
- [YouTube Data API v3](https://developers.google.com/youtube/v3)

## Support

For issues related to:
- **Deployment**: Open an issue in this repository
- **PiCam device setup**: See [AC Training Lab documentation](https://ac-training-lab.readthedocs.io/en/latest/devices/picam.html)
- **YouTube API**: Consult the [YouTube API documentation](https://developers.google.com/youtube/v3)
