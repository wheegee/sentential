# Partitions

> :warning: This document describes a key configuration for Sentential which is camping on the environment variable `PARTITION`. We will be changing this in the near future to something more wise like `SNTL_ENV`.

In deploying to the cloud, we enter a shared space. We must partition this space meaningfully so that my deployment doesn't interfere with your deployment.

By default, Sentential creates resources under a root namespace of your AWS ID. This ensures you will reside in your own namespace until you declare otherwise.

To switch your operative partition:

```shell
> PARTITION=<name> sntl
```