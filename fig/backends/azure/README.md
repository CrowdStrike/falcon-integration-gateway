# Azure Backend

Integration with Microsoft Azure Log Analytics.

### Example Configuration file

[config/config.ini](https://github.com/CrowdStrike/falcon-integration-gateway/blob/main/config/config.ini) is expected to configure Falcon Integration Gateway. Minimal configuration for Azure backend follows.
```
[main]
# Cloud backends that are enabled. The gateway will push events to the cloud providers specified below
backends=AZURE

[azure]
# Azure section is applicable only when AZURE backend is enabled in the [main] section.

# Uncomment to provide Azure Workspace ID. Alternatively, use WORKSPACE_ID env variable.
#workspace_id =
# Uncomment to provide Azure Primary Key. Alternatively, use PRIMARY_KEY env variable.
#primary_key =
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
       -e WORKSPACE_ID="$WORKSPACE_ID" \
       -e PRIMARY_KEY="$PRIMARY_KEY" \
       -e FALCON_CLOUD_REGION="us-1" \
       falcon-integration-gateway:latest
   ```

### Developer Resources
 - [Log Analytics Tutorial](https://docs.microsoft.com/en-us/azure/azure-monitor/logs/log-analytics-tutorial)
