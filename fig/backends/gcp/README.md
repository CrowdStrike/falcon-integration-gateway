# GCP Backend

Integration with Google Cloud Platform - Security Command Center.

### Example Configuration file

[config/config.ini](https://github.com/CrowdStrike/falcon-integration-gateway/blob/main/config/config.ini) is expected to configure Falcon Integration Gateway. Minimal configuration for Azure backend follows.
```
[main]
# Cloud backends that are enabled. The gateway will push events to the cloud providers specified below
backends=AZURE

[gcp]
# GCP section is applicable only when GCP backend is enabled in the [main] section.

# Use GOOGLE_APPLICATION_CREDENTIALS env variable to configure GCP Backend. GOOGLE_APPLICATION_CREDENTIALS
# is an environment variable used to configure GCP Service accounts, it should point out to the credentials
# file for given service account.
```

### Developer Guide

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
