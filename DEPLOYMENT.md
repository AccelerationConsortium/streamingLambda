# AWS Lambda Deployment Guide

This guide provides detailed instructions for deploying the YouTube streaming Lambda function directly to AWS without using Chalice.

## Prerequisites

Before you begin, ensure you have:

1. **AWS Account** with permissions to:
   - Create Lambda functions
   - Create and manage S3 buckets
   - Create IAM roles and policies
   - (Optional) Create Lambda Function URLs

2. **YouTube Data API v3 Credentials**:
   - A Google Cloud Project with YouTube Data API v3 enabled
   - OAuth 2.0 credentials configured for desktop application
   - A valid `token.pickle` file (generated after OAuth flow)

3. **S3 Bucket** for storing the YouTube API token

## Step 1: Obtain the Deployment Package

### Option A: Download from GitHub Releases (Recommended)

1. Go to the [Releases page](https://github.com/AccelerationConsortium/streamingLambda/releases)
2. Download the latest `deployment.zip` file

### Option B: Build Locally

1. Clone the repository:
   ```bash
   git clone https://github.com/AccelerationConsortium/streamingLambda.git
   cd streamingLambda
   ```

2. Run the build script:
   ```bash
   ./build-deployment-zip.sh
   ```

   This will create `deployment.zip` (~40MB) in the current directory.

## Step 2: Set Up S3 Bucket for YouTube Token

1. **Create an S3 bucket**:
   - Go to [S3 Console](https://console.aws.amazon.com/s3)
   - Click "Create bucket"
   - Choose a unique name (e.g., `my-org-youtube-token`)
   - Select your preferred region
   - Keep default settings for now
   - Click "Create bucket"

2. **Upload your token.pickle**:
   - Navigate to your bucket
   - Create a folder named `token`
   - Upload your `token.pickle` file to the `token/` folder
   - The full path should be: `s3://your-bucket-name/token/token.pickle`

3. **Note the bucket name** - you'll need it for configuration

## Step 3: Create IAM Role for Lambda

1. **Go to [IAM Console](https://console.aws.amazon.com/iam)**

2. **Create a new role**:
   - Click "Roles" → "Create role"
   - Select "AWS service" → "Lambda"
   - Click "Next"

3. **Attach policies**:
   - Search and attach: `AWSLambdaBasicExecutionRole` (for CloudWatch Logs)
   - Click "Next"

4. **Create custom policy for S3 access**:
   - Click "Create policy" (opens new tab)
   - Switch to JSON tab and paste:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "s3:GetObject",
           "s3:PutObject"
         ],
         "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME/token/token.pickle"
       }
     ]
   }
   ```
   - Replace `YOUR-BUCKET-NAME` with your actual bucket name
   - Click "Next: Tags" → "Next: Review"
   - Name it `youtube-lambda-s3-access`
   - Click "Create policy"

5. **Return to role creation tab**:
   - Refresh the policies list
   - Search for and attach `youtube-lambda-s3-access`
   - Click "Next"

6. **Name the role**:
   - Role name: `youtube-lambda-role`
   - Click "Create role"

## Step 4: Create Lambda Function

1. **Go to [Lambda Console](https://console.aws.amazon.com/lambda)**

2. **Create function**:
   - Click "Create function"
   - Select "Author from scratch"
   - Function name: `youtube-stream` (or your preferred name)
   - Runtime: **Python 3.11**
   - Architecture: x86_64
   - Under "Change default execution role":
     - Select "Use an existing role"
     - Choose `youtube-lambda-role` (created in Step 3)
   - Click "Create function"

3. **Upload deployment package**:
   - In the "Code" tab, click "Upload from" → ".zip file"
   - Click "Upload" and select your `deployment.zip`
   - Click "Save"
   - Wait for the upload to complete (may take a minute for 40MB file)

4. **Configure function settings**:
   - Click on "Configuration" tab → "General configuration" → "Edit"
   - **Memory**: 1024 MB (recommended)
   - **Timeout**: 1 minute (60 seconds)
   - Click "Save"

## Step 5: Configure Environment (if needed)

If your S3 bucket name or token path differs from the defaults, you need to update the configuration:

### Default values in the code:
- S3 Bucket: `ac-token-youtube-api`
- S3 Key: `token/token.pickle`
- Channel ID: `UCHBzCfYpGwoqygH9YNh9A6g`

### To customize:

1. Download and extract `deployment.zip`
2. Edit `chalicelib/ytb_api_utils.py`:
   ```python
   # Lines 9-13
   CHANNEL_ID = "your-youtube-channel-id"  # Optional: your channel ID
   S3_BUCKET = "your-bucket-name"          # Your S3 bucket name
   S3_KEY = "token/token.pickle"           # Path to token in S3
   ```
3. Rebuild the deployment package:
   ```bash
   cd dependencies
   zip -r ../deployment.zip .
   cd ..
   ```
4. Upload the new `deployment.zip` to Lambda

## Step 6: Create Function URL (Optional but Recommended)

To enable HTTP access to your Lambda function:

1. **In Lambda Console**, go to your function
2. Click "Configuration" → "Function URL"
3. Click "Create function URL"
4. **Auth type**:
   - `NONE` - Public access (simpler, less secure)
   - `AWS_IAM` - Requires AWS credentials (more secure)
5. Click "Save"
6. **Copy the Function URL** - you'll use this with your monitoring device

Example Function URL:
```
https://abcdefg123456.lambda-url.us-east-1.on.aws/
```

## Step 7: Test the Function

1. **In Lambda Console**, click "Test" tab
2. **Create new test event**:
   - Event name: `test-create-stream`
   - Event JSON:
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
3. Click "Save"
4. Click "Test"
5. Check the execution results:
   - Success: You should see a 200 status code with stream details
   - Failure: Check CloudWatch Logs for error details

## Step 8: Test via HTTP (if using Function URL)

Using curl:
```bash
curl -X POST https://YOUR-FUNCTION-URL/ \
  -H "Content-Type: application/json" \
  -d '{
    "body": {
      "action": "create",
      "cam_name": "Camera1",
      "workflow_name": "MyWorkflow",
      "privacy_status": "private"
    }
  }'
```

## API Reference

### Request Format

```json
{
  "body": {
    "action": "create" | "end",
    "cam_name": "string",
    "workflow_name": "string",
    "privacy_status": "public" | "private" | "unlisted"
  }
}
```

### Parameters

- **action** (required): 
  - `"create"` - Creates a new YouTube live broadcast
  - `"end"` - Ends active broadcasts for the workflow
  
- **cam_name** (optional): Name of the camera/device (default: "UnknownCam")

- **workflow_name** (required): Identifier for your workflow. Used to:
  - Group related streams
  - Create/find playlists
  - End specific broadcasts

- **privacy_status** (optional): Video privacy setting (default: "private")
  - `"public"` - Anyone can watch
  - `"private"` - Only you can watch
  - `"unlisted"` - Anyone with the link can watch

### Response Format

#### Success Response (action: create)
```json
{
  "statusCode": 200,
  "body": {
    "status": "created",
    "result": {
      "broadcast_id": "...",
      "video_id": "...",
      "stream_id": "...",
      "playlist_id": "...",
      "title": "...",
      "privacy_status": "private",
      "ffmpeg_url": "rtmp://...",
      "video_url": "https://www.youtube.com/watch?v=...",
      "playlist_add_status": "added"
    }
  }
}
```

#### Success Response (action: end)
```json
{
  "statusCode": 200,
  "body": {
    "status": "ended",
    "message": "WorkflowName ended successfully"
  }
}
```

#### Error Response
```json
{
  "statusCode": 400,
  "body": {
    "error": "Error description"
  }
}
```

## Monitoring and Logs

1. **CloudWatch Logs**:
   - Go to [CloudWatch Console](https://console.aws.amazon.com/cloudwatch)
   - Navigate to "Logs" → "Log groups"
   - Find `/aws/lambda/youtube-stream` (or your function name)
   - View recent invocations and error messages

2. **Lambda Metrics**:
   - In Lambda Console, click "Monitor" tab
   - View invocation count, duration, errors, and throttles

## Troubleshooting

### Common Issues

**1. "No valid credentials available"**
- Check that `token.pickle` exists in S3 at the correct path
- Verify the Lambda role has S3 read/write permissions
- Ensure the token hasn't been revoked in Google Cloud Console

**2. "Access Denied" to S3**
- Verify the IAM role has the correct S3 permissions
- Check bucket name and key path match the code configuration

**3. "Task timed out after 3.00 seconds"**
- Increase Lambda timeout to 60 seconds (see Step 4)
- Check network connectivity to YouTube API

**4. "Invalid JSON or internal error"**
- Verify request format matches the API reference
- Check CloudWatch Logs for detailed error messages

### Getting Help

- **GitHub Issues**: [Report a bug](https://github.com/AccelerationConsortium/streamingLambda/issues)
- **Documentation**: [AC Training Lab](https://ac-training-lab.readthedocs.io/en/latest/devices/picam.html)
- **YouTube API**: [YouTube Data API v3 Docs](https://developers.google.com/youtube/v3)

## Security Best Practices

1. **Use IAM authentication** for Function URLs when possible
2. **Restrict S3 bucket access** to only the Lambda role
3. **Enable CloudTrail** to audit Lambda invocations
4. **Rotate credentials** regularly in Google Cloud Console
5. **Use private** or **unlisted** privacy status for sensitive streams
6. **Monitor costs** - YouTube API has quota limits

## Updating the Function

To update your Lambda function with new code:

1. Download/build the latest `deployment.zip`
2. Go to Lambda Console → your function
3. Click "Upload from" → ".zip file"
4. Select the new `deployment.zip`
5. Click "Save"

The function will be updated without downtime.

## Cost Considerations

- **Lambda**: First 1M requests/month are free, then $0.20 per 1M requests
- **S3**: Minimal costs for storing one small file
- **Data Transfer**: Charges may apply for data transfer out
- **YouTube API**: Free tier includes 10,000 quota units/day

For most use cases, costs should be less than $1/month.
