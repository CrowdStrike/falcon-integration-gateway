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

# Uncomment to provide Google Service Account filepath. Alternatively, use GOOGLE_SERVICE_ACCOUNT_FILE variable
#service_account = apikeys-demo.json

# Uncomment to provide Chronicle Customer ID. Alternatively, use GOOGLE_CUSTOMER_ID variable
#customer_id = XXX

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
       -e GOOGLE_SERVICE_ACCOUNT_FILE="$GOOGLE_SERVICE_ACCOUNT_FILE" \
       -e GOOGLE_CUSTOMER_ID="$GOOGLE_CUSTOMER_ID" \
       -e CHRONICLE_REGION="$CHRONICLE_REGION" \
       -e FALCON_CLOUD_REGION="us-1" \
       falcon-integration-gateway:latest
   ```
