#!/bin/bash

# 1. Set Project Variables
export PROJECT_ID="ai-commerce-search-ni-osaka"
export REGION="us-central1"
export REPO_NAME="mcp-commerce"
export IMAGE_NAME="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/mcp-commerce-server"

# 2. Build the Container
gcloud builds submit --project $PROJECT_ID --tag $IMAGE_NAME

# 3. Deploy to Cloud Run (Securely)
gcloud run deploy mcp-commerce \
  --project $PROJECT_ID \
  --image $IMAGE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars PROJECT_ID=$PROJECT_ID,LOCATION=global,CATALOG=default_catalog

