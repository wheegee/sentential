# Envs & Secrets

When running an application we generally want secrets and configurations in our environment. Sentential makes this easy through the `sntl envs` & `sntl secrets` commands.

The only difference between the `envs` store and the `secrets` store is that the `secrets` values are encryped with kms.

> :lock: By default `aws/ssm` KMS key is used to encrypt `secrets`, this can be modified via the `AWS_KMS_KEY_ALIAS` environment variable.

### Prerequisites

You have initialized the [explore project](/explore/project) and are operating in said directory.

### Env store

Let's write an environment variable to the env store and read it back...

```bash
> sntl envs set USERNAME non-root
> sntl secrets set PASSWORD is-encrypted
> sntl envs ls

  key        value       description   validation  
 ───────────────────────────────────────────────── 
  USERNAME   non-root    None          None        


> sntl secrets ls

  key        value          description   validation  
 ───────────────────────────────────────────────── 
  PASSWORD   is-encrypted   None          None        
```

This is the most basic usage of a larger concept, for more see [Stores & Shapes](/examples/shapes).

### Develop

Create or modify...

<!-- tabs:start -->

#### **./src/app.py**

```python
from os import environ

def handler(event, context):
    return {
      "username": environ["USERNAME"],
      "password": "PASSWORD" in environ
    }
```

<!-- tabs:end -->

### Build

```bash
> sntl build
```

### Verify

```bash
> sntl deploy local
> sntl invoke local '{}'

{
  "ResponseMetadata": {
    "HTTPStatusCode": 200,
    "HTTPHeaders": {
      "date": "Wed, 01 Feb 2023 03:59:16 GMT",
      "content-length": "19",
      "content-type": "text/plain; charset=utf-8"
    },
    "RetryAttempts": 0
  },
  "StatusCode": 200,
  "Payload": "{ \"username\": \"non-root\", \"password\": true }"
}
```

### Publish

```bash
> sntl publish
```

### Deploy

```bash
> sntl deploy aws
> sntl invoke aws '{}'

{
  "ResponseMetadata": {
    "RequestId": "somerequestid",
    "HTTPStatusCode": 200,
    "HTTPHeaders": {
      "date": "Wed, 01 Feb 2023 03:58:33 GMT",
      "content-type": "application/json",
      "content-length": "19",
      "connection": "keep-alive",
      "x-amzn-*": "various amz headers"
    },
    "RetryAttempts": 0
  },
  "StatusCode": 200,
  "Payload": "{ \"username\": \"non-root\", \"password\": true }"
}

```

### Cleanup

```bash
> sntl destroy aws
> sntl envs clear
> sntl secrets clear
```
