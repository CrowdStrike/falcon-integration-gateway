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

# Uncomment to provide Google security key. Alternatively, use GOOGLE_SECURITY_KEY env variable
#security_key =

# Uncomment to provide Chronicle region (us, europe, asia-southeast1). Alternatively, use CHRONICLE_REGION variable
#region =
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
       -e CHRONICLE_REGION="$CHRONICLE_REGION" \
       -e FALCON_CLOUD_REGION="us-1" \
       falcon-integration-gateway:latest
   ```
