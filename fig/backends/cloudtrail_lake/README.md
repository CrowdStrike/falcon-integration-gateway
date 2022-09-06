# AWS CloudTrail Lake Backend

Integration with AWS CloudTrail Lake.

### Example Configuration file

[config/config.ini](https://github.com/CrowdStrike/falcon-integration-gateway/blob/main/config/config.ini) configures Falcon Integration Gateway. Below is a minimal configuration example for AWS CloudTrail Lake:
```
[main]
# Cloud backends that are enabled. The gateway will push events to the cloud providers specified below
backends=CLOUDTRAIL_LAKE

[cloudtrail_lake]
# AWS CloudTrail Lake section is applicable only when CLOUDTRAIL_LAKE backend is enabled in the [main] section.

# Uncomment to provide the Channel ARN. Alternatively, use CHANNEL_ARN env variable.
#channel_arn =
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
       -e CHANNEL_ARN="$CHANNEL_ARN" \
       -v ~/.aws:/fig/.aws \
       falcon-integration-gateway:latest
   ```
