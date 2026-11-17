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

# Uncomment to verify the syslog server against this PEM file instead of the system CA store.
# Alternatively, use SYSLOG_CA_FILE env variable
#syslog_ca_file =

```

### TLS certificate verification

The gateway verifies the syslog server's TLS certificate and refuses to send events to a server it can't verify.
Each event includes the Workspace One token, so an unverified connection would expose it to anyone able to
intercept the traffic.

- By default the certificate must chain to a CA in the system trust store, and `syslog_host` must match a DNS
  name in the certificate's Subject Alternative Name (SAN). Use the host name, not an IP address, unless the
  certificate lists that IP address.
- If the syslog server uses a private CA or a self-signed certificate, set `syslog_ca_file` (or `SYSLOG_CA_FILE`)
  to a PEM file with that CA certificate, or with the server's own certificate if it's self-signed.
  The file **replaces** the system trust store, so publicly trusted CAs aren't used while it's set.
- When the certificate can't be verified, the gateway logs `TLS handshake with syslog collector ... failed`
  and doesn't send the event. Fix the configuration and restart the gateway.

You can see what certificate the server presents, and check it against the file you plan to use:
```
openssl s_client -connect "$SYSLOG_HOST:6514" -servername "$SYSLOG_HOST" -verify_hostname "$SYSLOG_HOST" \
    -CAfile /path/to/ca.pem </dev/null
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
 - Run the application with a private CA or self-signed syslog certificate
   ```
   docker run -it --rm \
       -e FALCON_CLIENT_ID="$FALCON_CLIENT_ID" \
       -e FALCON_CLIENT_SECRET="$FALCON_CLIENT_SECRET" \
       -e WORKSPACEONE_TOKEN="$WORKSPACEONE_TOKEN" \
       -e SYSLOG_HOST="$SYSLOG_HOST" \
       -e SYSLOG_CA_FILE=/fig/certs/syslog-ca.pem \
       -v /path/to/syslog-ca.pem:/fig/certs/syslog-ca.pem:ro \
       -e FALCON_CLOUD_REGION="us-1" \
       falcon-integration-gateway:latest
   ```
