# Python

### Prerequisites

You have initialized the [explore project](/explore/project) and are operating in said directory.

### Develop

Create or modify...

<!-- tabs:start -->

#### **./src/app.py**

```python
import sys
def handler(event, context): 
    return f"echo: {event}"
```

#### **./lambda-entrypoint.sh**

```bash
#!/bin/sh

if [ $# -ne 1 ]; then
  echo "entrypoint requires the handler name to be the first argument" 1>&2
  exit 142
fi

if [ -z "${AWS_LAMBDA_RUNTIME_API}" ]; then
    exec /usr/local/bin/aws-lambda-rie /usr/local/bin/python -m awslambdaric $1
else
    exec /usr/local/bin/python -m awslambdaric $1
fi
```

#### **./Dockerfile**

```dockerfile
# We will extract sentential requirements from this image
FROM ghcr.io/wheegee/entry:latest as entry

# We will extract AWS Lambda runtime interface emulator from this image
FROM public.ecr.aws/lambda/provided:latest AS aws

FROM python AS runtime
# Standard AWS Lambda image configuration
ENV LAMBDA_RUNTIME_DIR=/var/runtime
ENV LAMBDA_TASK_ROOT=/var/task
WORKDIR ${LAMBDA_TASK_ROOT}

# Install sentential requirements
ENV AWS_LAMBDA_EXEC_WRAPPER=/bin/wrapper.sh
COPY --chmod=755 --from=entry / /bin/

# Install runtime interface emulator
COPY --from=aws --chmod=755 /usr/local/bin/aws-lambda-rie /usr/local/bin/aws-lambda-rie

# Install python runtime interface client
RUN pip install awslambdaric 

# Setup entrypoint
COPY --chmod=755 lambda-entrypoint.sh /lambda-entrypoint.sh
ENTRYPOINT [ "/lambda-entrypoint.sh" ]

FROM runtime AS explore
COPY src/ ${LAMBDA_TASK_ROOT}

# insert application specific build steps here

CMD ["app.handler"]
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
      "date": "Fri, 03 Feb 2023 18:19:25 GMT",
      "content-length": "11",
      "content-type": "text/plain; charset=utf-8"
    },
    "RetryAttempts": 0
  },
  "StatusCode": 200,
  "Payload": "\"echo: {}\""
}
```

### Further reading

- [custom runtime docs](https://docs.aws.amazon.com/lambda/latest/dg/runtimes-walkthrough.html)
- [runtime interface clients](https://docs.aws.amazon.com/lambda/latest/dg/runtimes-images.html#runtimes-api-client)
- [runtime interface emulator](https://github.com/aws/aws-lambda-runtime-interface-emulator)
