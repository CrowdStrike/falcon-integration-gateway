# falcon-integration-gateway [![Python Lint](https://github.com/CrowdStrike/falcon-integration-gateway/actions/workflows/linting.yml/badge.svg)](https://github.com/CrowdStrike/falcon-integration-gateway/actions/workflows/linting.yml) [![Container Build on Quay](https://quay.io/repository/crowdstrike/falcon-integration-gateway/status "Docker Repository on Quay")](https://quay.io/repository/crowdstrike/falcon-integration-gateway)

Falcon Integration Gateway for GCP Security Command Center forwards findings from CrowdStrike Falcon platform
to GCP Security Command Center.

Status: This is pre-release version (WIP).

## Deployment Guide

- [Deployment to GKE](docs/deployment-gke.md)

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
 - [Google Cloud Python Client](https://github.com/googleapis/google-cloud-python)
 - [Understanding Google Cloud Resource hierarchy](https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy)
 - [GCP SCC: API Explorer](https://developers.google.com/apis-explorer/#p/securitycenter/v1/)
 - [GCP SCC: How to Create & manage Security Findings](https://cloud.google.com/security-command-center/docs/how-to-api-create-manage-findings)
