# Humio Backend

Integration with Humio - sends events to Humio

### Example Configuration file

[config/config.ini](https://github.com/CrowdStrike/falcon-integration-gateway/blob/main/config/config.ini)  configures Falcon Integration Gateway. Below is a minimal configuration example for HUMIO:
```
[main]
# Cloud backends that are enabled. The gateway will push events to the cloud providers specified below
backends=HUMIO

[humio]
# TODO ingestion token configuration
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
       -e HUMION_TOKEN="$HUMIO_TOKEN" \
       falcon-integration-gateway:latest
   ```

### Developer Resources
 - [Humio Ingest API Reference](https://library.humio.com/stable/reference/api/ingest-api/)
 - [python-humio library](https://github.com/humio/python-humio)
