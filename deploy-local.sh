#!/bin/bash
# Deploy using local cloudbuild.yaml with real values

# Check if cloudbuild.local.yaml exists
if [ ! -f "cloudbuild.local.yaml" ]; then
    echo "Error: cloudbuild.local.yaml not found!"
    echo "Please create this file with your actual deployment values."
    exit 1
fi

# Deploy using the local configuration
gcloud builds submit --config=cloudbuild.local.yaml

echo "Deployment completed using local configuration with real values."
