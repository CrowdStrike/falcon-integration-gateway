# Backends for Falcon Integration Gateway

Falcon Integration Gateway may push information to various backends. Backends needs to be explicitly enabled in configuration file. Example:

```
[main]
backends=AZURE,GCP
```

## Currently Available Backends

 * [Azure (Log Analytics)](azure)
 * [GCP (Security Command Center)](gcp)
