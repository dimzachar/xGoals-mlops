#!/usr/bin/env bash

echo "publishing image ${LOCAL_IMAGE_NAME} to ECR..."
# you would need to replace
export ECR_IMAGE=###
aws ecr get-login-password --region eu-central-1 | docker login --username AWS --password-stdin ${ECR_IMAGE}
docker tag ${LOCAL_IMAGE_NAME} ${ECR_IMAGE}/${ECR_REGISTRY}:latest
docker push ${ECR_IMAGE}/${ECR_REGISTRY}:latest


