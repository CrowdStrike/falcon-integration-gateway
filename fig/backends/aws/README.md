# AWS Backend

Integration with AWS Security Hub.

Single Falcon Integration Gateway can be used to send reports from all AWS regions to single AWS Security Hub region.

### Example Configuration file

[config/config.ini](https://github.com/CrowdStrike/falcon-integration-gateway/blob/main/config/config.ini)  configures Falcon Integration Gateway. Below is a minimal configuration example for AWS:
```
[main]
# Cloud backends that are enabled. The gateway will push events to the cloud providers specified below
backends=AWS

[aws]
# AWS section is applicable only when AWS backend is enabled in the [main] section.

# Uncomment to provide aws region. Alternatively, use AWS_REGION env variable
#region=eu-west-1
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
       -v ~/.aws:/fig/.aws \
       falcon-integration-gateway:latest
   ```
