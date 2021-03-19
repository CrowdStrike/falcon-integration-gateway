# falcon-integration-gateway [![Python Lint](https://github.com/CrowdStrike/falcon-integration-gateway/actions/workflows/linting.yml/badge.svg)](https://github.com/CrowdStrike/falcon-integration-gateway/actions/workflows/linting.yml)

Falcon Integration Gateway for GCP Security Command Center forwards findings from CrowdStrike Falcon platform
to GCP Security Command Center.

Status: This is pre-release version (WIP).



## Deployment Guide

### Prerequisites:

 - Have CrowdStrike CWP Subscription
 - Have Security Command Center enabled in google cloud.
 - Have GCP workloads registered with CrowdStrike Falcon platform.
 - Have `gcloud` tool installed locally or use [cloud-tools-image](https://github.com/CrowdStrike/cloud-tools-image)

### Step 1: Create new CrowdStrike API Key Pairs

https://falcon.crowdstrike.com/support/api-clients-and-keys.

### Step 2: Create new GCP Service Account

https://cloud.google.com/security-command-center/docs/how-to-programmatic-access

```
export PROJECT_ID=$(gcloud config get-value project)
export PROJECT_NUMBER=$(gcloud projects list --filter="$PROJECT" --format="value(PROJECT_NUMBER)")
export ORG_ID="$(gcloud projects get-ancestors $PROJECT_ID | grep organization | cut -f1 -d' ')"
export SERVICE_ACCOUNT=falcon-integration-gateway
export KEY_LOCATION="./gcloud-secret-${SERVICE_ACCOUNT}.json"


# Create service account for this project
gcloud iam service-accounts create $SERVICE_ACCOUNT  --display-name \
 "Service Account for [USER]"  --project $PROJECT_ID

# Create key for the service account
gcloud iam service-accounts keys create $KEY_LOCATION  --iam-account \
 $SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com

# Grant the service account the securitycenter.admin role for the organization.
gcloud organizations add-iam-policy-binding $ORG_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com" \
  --role='roles/securitycenter.admin'
```

### Step 3: Enable security Command Center API in your projects

If your project has never had API for SCC enabled, chances are you will have to visit the following URL and enable API manually. https://console.cloud.google.com/apis/library/securitycenter.googleapis.com

### Step 4: Deploy the container image

TODO

## Developer Guide

### Local Container Instructions
 - Build the image
   ```
   docker build . -t falcon-integration-gateway
   ```
 - Run the application
   ```
   docker run -it --rm \
       -e FALCON_CLIENT_ID="$FALCON_CLIENT_ID" \
       -e FALCON_CLIENT_SECRET="$FALCON_CLIENT_SECRET" \
       -e FALCON_CLOUD_REGION="us-1" \
       -e GOOGLE_APPLICATION_CREDENTIALS=/gcloud/gcloud-secret-falcon-integration-gateway.json \
       -v ~/.config/gcloud:/gcloud/ \
       falcon-integration-gateway:latest
   ```

### Developer Resources
 - [GCP SCC API Explorer](https://developers.google.com/apis-explorer/#p/securitycenter/v1/)
