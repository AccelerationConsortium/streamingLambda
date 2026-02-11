#!/bin/bash

# Build script for creating AWS Lambda deployment package
# This script creates a deployment.zip file that can be uploaded directly to AWS Lambda

set -e

echo "Building AWS Lambda deployment package..."

# Clean up any existing artifacts
echo "Cleaning up existing artifacts..."
rm -rf dependencies deployment.zip

# Create dependencies directory
echo "Creating dependencies directory..."
mkdir -p dependencies

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --target ./dependencies \
  boto3 \
  google-api-python-client \
  google-auth \
  google-auth-oauthlib \
  google-auth-httplib2

# Copy lambda function and chalicelib
echo "Copying lambda function and chalicelib..."
cp lambda_function.py dependencies/
cp -r chalicelib dependencies/

# Create deployment package
echo "Creating deployment.zip..."
cd dependencies
zip -q -r ../deployment.zip .
cd ..

# Get the size of the deployment package
SIZE=$(du -h deployment.zip | cut -f1)
echo "✓ deployment.zip created successfully (${SIZE})"
echo ""
echo "You can now upload deployment.zip to AWS Lambda!"
echo "See README.md for detailed deployment instructions."
