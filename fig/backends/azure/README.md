# Azure Backend

Integration with Microsoft Azure Log Analytics.

### Example Configuration file

[config/config.ini](https://github.com/CrowdStrike/falcon-integration-gateway/blob/main/config/config.ini) configures Falcon Integration Gateway. Below is a minimal configuration example for Azure:
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

# Uncoment to enable RTR based auto discovery of Azure Arc Systems
# arc_autodiscovery = true
```

### Azure Arc Autodiscovery

Azure Arc is service within Microsoft Azure that allows users to connect and manage systems outside Azure using single pane of glass (Azure user interface).

Falcon Integration Gateway is able to identify Azure Arc system properties (resourceName, resourceGroup, subscriptionId, tenantId, and vmId) using RTR and send these details over to Azure Log Analytics.

To enable this feature:
 - set `azure_autodiscovery=true` in config.ini
 - grant extra Falcon permission to API keys in CrowdStrike Falcon
    - Real Time Response: [Read, Write]

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
