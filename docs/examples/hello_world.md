# Hello World

Let's deploy a simple `echo` style function to aquaint ourselves with Sentential.

### Prerequisites

You have initialized the [explore project](/examples/project?id=explore-project-setup) and are operating in said directory.

### Develop

Create or modify...

<!-- tabs:start -->

#### **./src/app.py**

```python
def handler(event, context):
     return f"echo: {event}"
```

<!-- tabs:end -->

### Build


```bash
> sntl build
```

### Verify

```bash
> sntl deploy local
> sntl invoke local '{ "hello": "world" }'

{
  "ResponseMetadata": {
    "HTTPStatusCode": 200,
    "HTTPHeaders": {
      "date": "Wed, 01 Feb 2023 00:35:35 GMT",
      "content-length": "26",
      "content-type": "text/plain; charset=utf-8"
    },
    "RetryAttempts": 0
  },
  "StatusCode": 200,
  "Payload": "\"echo: {'hello': 'world'}\""
}
```

### Publish

```bash
> sntl login
> sntl publish
```

### Deploy

```bash
> sntl deploy aws
> sntl invoke aws '{ "hello": "world!" }'

{
  "ResponseMetadata": {
    "RequestId": "somerequestid",
    "HTTPStatusCode": 200,
    "HTTPHeaders": {
      "date": "Wed, 01 Feb 2023 03:50:07 GMT",
      "content-type": "application/json",
      "content-length": "27",
      "connection": "keep-alive",
      "x-amzn-*": "various amz headers"
    },
    "RetryAttempts": 0
  },
  "StatusCode": 200,
  "Payload": "\"echo: {'hello': 'world!'}\""
}
```

### Cleanup

```bash
> sntl destroy local
> sntl destroy aws
```
