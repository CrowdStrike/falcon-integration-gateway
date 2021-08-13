# Humio Backend

Integration with Humio - sends events to Humio

### Example Configuration file

[config/config.ini](https://github.com/CrowdStrike/falcon-integration-gateway/blob/main/config/config.ini)  configures Falcon Integration Gateway. Below is a minimal configuration example for HUMIO:
```
[main]
# Cloud backends that are enabled. The gateway will push events to the cloud providers specified below
backends=HUMIO

[humio]
# Humio section is applicable only when Humio backend is enabled in the [main] section

# Uncomment to provide your Humio host (defaults to cloud.humio.com). Alternatively, use HUMIO_HOST env variable
# host =

# Uncomment to provide your Humio port (defaults to 443). Alternatively, use HUMIO_PORT env variable
# port =

# Uncomment to provide ingest token. Alternatively, use HUMIO_INGEST_TOKEN env variable
# ingest_token =
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
       -e HUMION_INGEST_TOKEN="$HUMIO_TOKEN" \
       falcon-integration-gateway:latest
   ```

### Developer Resources
 - [Humio Ingest API Reference](https://library.humio.com/stable/reference/api/ingest-api/)
 - [python-humio library](https://github.com/humio/python-humio)
