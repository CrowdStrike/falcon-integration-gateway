# Backends for Falcon Integration Gateway

Falcon Integration Gateway may push information to various backends. Backends needs to be explicitly enabled in configuration file. Example:

```
[main]
backends=AWS,AZURE,GCP,WORKSPACEONE
```

## Currently Available Backends

 * [AWS](aws)
 * [Azure(Log Analytics)](azure)
 * [GCP(Security Command Center)](gcp)
 * [WorkspaceOne](workspaceone)

