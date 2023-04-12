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
    exec /usr/bin/aws-lambda-rie /usr/bin/python3 -m awslambdaric $1
else
    exec /usr/bin/python3 -m awslambdaric $1
fi
```

#### **./Dockerfile**

```dockerfile
FROM alpine:3.16 AS python
# Install python
RUN apk add --no-cache \
    python3 \
    py3-pip \
    python3-dev
# Install native build dependencies
RUN apk add --no-cache \
    libstdc++ \
    build-base \
    libtool \
    autoconf \
    automake \
    libexecinfo-dev \
    make \
    cmake \
    libcurl

FROM python AS runtime
ENV LAMBDA_RUNTIME_DIR=/var/runtime
ENV LAMBDA_TASK_ROOT=/var/task
ENV AWS_LAMBDA_EXEC_WRAPPER=/bin/wrapper.sh
WORKDIR ${LAMBDA_TASK_ROOT}
# Install python lambda runtime interface client
RUN pip install awslambdaric
# Install runtime interface emulator
COPY --from=public.ecr.aws/lambda/provided:latest --chmod=755 /usr/local/bin/aws-lambda-rie /usr/bin/aws-lambda-rie
# Install sentential requirements
# Note: if you have problems, check that this entry semver is up to date
# https://github.com/wheegee/entry
COPY --chmod=755 --from=ghcr.io/wheegee/entry:0.4.1 / /bin/
COPY --chmod=755 lambda-entrypoint.sh /lambda-entrypoint.sh
# Set up entrypoint
ENTRYPOINT [ "/lambda-entrypoint.sh" ]

FROM runtime AS explore
COPY src/ ${LAMBDA_TASK_ROOT}
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