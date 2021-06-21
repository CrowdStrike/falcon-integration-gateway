# Workspace One Backend

Integration with Workspace One Intelligence.

### Example Configuration file

[config/config.ini](https://github.com/CrowdStrike/falcon-integration-gateway/blob/main/config/config.ini) configures Falcon Integration Gateway. Below is a minimal configuration example for Workspace One:
```
[main]
# Cloud backends that are enabled. The gateway will push events to the cloud providers specified below
backends=WORKSPACEONE

[workspaceone]
# Workspace One section is applicable only when Workspace One backend is enabled in the [main] section.

# Uncomment to provide Workspace One token. Alternatively, use WORKSPACEONE_TOKEN env variable
#token=

# Uncomment to provide syslog host. Alternatively, use SYSLOG_HOST env variable
#syslog_host = 

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
       -e WORKSPACEONE_TOKEN="$WORKSPACEONE_TOKEN" \
       -e SYSLOG_HOST="$SYSLOG_HOST" \
       -e FALCON_CLOUD_REGION="us-1" \
       falcon-integration-gateway:latest
   ```
