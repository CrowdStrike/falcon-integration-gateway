# Generic Backend

The GENERIC backend outputs events to STDOUT, making it ideal for:

- **Testing** - Verify FIG is receiving events before deploying to production backends
- **Debugging** - Inspect raw event data and troubleshoot integration issues
- **Development** - Test new backend implementations or configuration changes

> **Note:** This backend is not recommended for production use.

## Configuration

### Basic Setup

[config/config.ini](https://github.com/CrowdStrike/falcon-integration-gateway/blob/main/config/config.ini) configures Falcon Integration Gateway. Below is a minimal configuration example for GENERIC backend:

```ini
[main]
backends = GENERIC
```

### Event Type Filtering

By default, the GENERIC backend processes ALL event types. You can filter to specific event types using the `event_types` option:

| Option        | Environment Variable  | Default | Description                                              |
|:--------------|:----------------------|:--------|:---------------------------------------------------------|
| `event_types` | `GENERIC_EVENT_TYPES` | `ALL`   | Comma-separated list of event types to process, or `ALL` |

**Common event types:**

- `EppDetectionSummaryEvent` - Detection/threat events
- `AuthActivityAuditEvent` - Authentication/audit events

**Examples:**

Process all events (default):

```ini
[generic]
event_types = ALL
```

Process only detection events:

```ini
[generic]
event_types = EppDetectionSummaryEvent
```

Process multiple specific event types:

```ini
[generic]
event_types = EppDetectionSummaryEvent,AuthActivityAuditEvent
```

Or via environment variable:

```bash
export GENERIC_EVENT_TYPES="EppDetectionSummaryEvent,AuthActivityAuditEvent"
```

## Developer Guide

1. Build the image

    ```shell
    docker build . -t falcon-integration-gateway
    ```

2. Run the application

    ```shell
    docker run -it --rm \
        -e FALCON_CLIENT_ID="$FALCON_CLIENT_ID" \
        -e FALCON_CLIENT_SECRET="$FALCON_CLIENT_SECRET" \
        -e FALCON_CLOUD_REGION="us-1" \
        -e FIG_BACKENDS=GENERIC \
        falcon-integration-gateway:latest
    ```

3. Run with event type filtering (optional)

    ```shell
    docker run -it --rm \
        -e FALCON_CLIENT_ID="$FALCON_CLIENT_ID" \
        -e FALCON_CLIENT_SECRET="$FALCON_CLIENT_SECRET" \
        -e FALCON_CLOUD_REGION="us-1" \
        -e FIG_BACKENDS=GENERIC \
        -e GENERIC_EVENT_TYPES="EppDetectionSummaryEvent" \
        falcon-integration-gateway:latest
    ```
