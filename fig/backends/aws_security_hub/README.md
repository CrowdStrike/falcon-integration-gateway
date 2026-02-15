# AWS Security Hub+ Backend

Integration with AWS Security Hub+ using the OCSF 1.6 schema and BatchImportFindingsV2 API.

> [!IMPORTANT]
> By default, this backend only supports detection events that originate from AWS. However, with the `accept_all_events=true` configuration option, it can process all events regardless of source. Alternatively, you can use the `AWS_SECURITY_HUB_ACCEPT_ALL_EVENTS` environment variable.

### Example Configuration file

[config/config.ini](https://github.com/CrowdStrike/falcon-integration-gateway/blob/main/config/config.ini) configures Falcon Integration Gateway. Below is a minimal configuration example for AWS Security Hub+:

```ini
[main]
# Cloud backends that are enabled. The gateway will push events to the cloud providers specified below
backends=AWS_SECURITY_HUB

[aws_security_hub]
# AWS Security Hub (OCSF) section is applicable only when AWS_SECURITY_HUB backend is enabled.
# Uses OCSF 1.6 schema and BatchImportFindingsV2 API.

# Uncomment to provide AWS region. Alternatively, use AWS_SECURITY_HUB_REGION env variable.
#region = us-west-2

# Uncomment to accept events from any source (default: false).
# Alternatively, use AWS_SECURITY_HUB_ACCEPT_ALL_EVENTS env variable.
#accept_all_events = false
```

### Developer Guide

- Build the image

   ```bash
   docker build . -t falcon-integration-gateway
   ```

- Run the application

   ```bash
   docker run -it --rm \
       -e FALCON_CLIENT_ID="$FALCON_CLIENT_ID" \
       -e FALCON_CLIENT_SECRET="$FALCON_CLIENT_SECRET" \
       -e FALCON_CLOUD_REGION="us-1" \
       -e FIG_BACKENDS=AWS_SECURITY_HUB \
       -e AWS_SECURITY_HUB_REGION="us-west-2" \
       -v ~/.aws:/fig/.aws \
       falcon-integration-gateway:latest
   ```
