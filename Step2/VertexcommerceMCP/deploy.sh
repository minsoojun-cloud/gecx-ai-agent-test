#!/bin/bash

# 1. Set Project Variables
export PROJECT_ID="retail-search-jp-demo-minsoo"
export IMAGE_NAME="gcr.io/$PROJECT_ID/mcp-commerce-server-minsoo"

# 2. Build the Container
gcloud builds submit --tag $IMAGE_NAME

# 3. Deploy to Cloud Run (Securely)
gcloud run deploy mcp-commerce-for-agent \
  --image $IMAGE_NAME \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars PROJECT_ID=$PROJECT_ID,LOCATION=global,CATALOG=default_catalog