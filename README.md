# falcon-integration-gateway [![Python Lint](https://github.com/CrowdStrike/falcon-integration-gateway/actions/workflows/linting.yml/badge.svg)](https://github.com/CrowdStrike/falcon-integration-gateway/actions/workflows/linting.yml) [![Container Build on Quay](https://quay.io/repository/crowdstrike/falcon-integration-gateway/status "Docker Repository on Quay")](https://quay.io/repository/crowdstrike/falcon-integration-gateway)

Falcon Integration Gateway forwards findings from CrowdStrike Falcon platform to various [backends](fig/backends).

Status: This is pre-release version (WIP).

## Deployment Guide

- [Deployment to AKS](docs/aks)
- [Deployment to GKE](docs/gke)

## Developer Guide

Start with learning about the [backends](fig/backends).

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
