# YouTube Streaming Lambda Function

This repository provides an AWS Lambda function for automatic YouTube livestream creation and management from [monitoring devices](https://ac-training-lab.readthedocs.io/en/latest/devices/picam.html).

## Deployment Options

### Option 1: Direct AWS Lambda Deployment (Recommended for external users)

This method allows you to deploy the Lambda function directly to AWS without requiring Chalice or any special deployment tools. Perfect for users outside the Acceleration Consortium who want to set up their own YouTube streaming Lambda function.

📖 **[See DEPLOYMENT.md for detailed step-by-step instructions](DEPLOYMENT.md)**

#### Quick Start

1. **Download the deployment package**
   
   Go to the [Releases](../../releases) page and download the latest `deployment.zip` file.
   
   Or build it locally:
   ```bash
   git clone https://github.com/AccelerationConsortium/streamingLambda.git
   cd streamingLambda
   ./build-deployment-zip.sh
   ```

2. **Upload to AWS Lambda and Configure**
   
   Follow the [detailed deployment guide](DEPLOYMENT.md) for complete instructions on:
   - Creating IAM roles with proper permissions
   - Uploading the deployment package
   - Configuring function settings
   - Setting up S3 bucket for YouTube token
   - Creating a Function URL
   - Testing the function

3. **Use with your monitoring device**
   
   Once deployed, use the Lambda Function URL with your [PiCam device](https://ac-training-lab.readthedocs.io/en/latest/devices/picam.html).

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
