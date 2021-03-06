# Chronicle Backend

Integration with Chronicle.

### Example Configuration file

[config/config.ini](https://github.com/CrowdStrike/falcon-integration-gateway/blob/main/config/config.ini) configures Falcon Integration Gateway. Below is a minimal configuration example for Chronicle:
```
[main]
# Cloud backends that are enabled. The gateway will push events to the cloud providers specified below
backends=CHRONICLE

[chronicle]
# Chronicle section is applicable only when Chronicle backend is enabled in the [main] section

# Uncomment to provide Google security key. Alternatively, use GOOGLE_SECURITY_KEY variable
#security_key =

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
       -e GOOGLE_SECURITY_KEY="$GOOGLE_SECURITY_KEY" \
       -e FALCON_CLOUD_REGION="us-1" \
       falcon-integration-gateway:latest
   ```