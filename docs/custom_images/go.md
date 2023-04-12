# Go

### Prerequisites

You have initialized the [explore project](/explore/project) and are operating in said directory.

### Develop

Create or modify...

<!-- tabs:start -->

#### **./src/main.go**

```go
package main

import (
    "fmt"
    "context"
    "github.com/aws/aws-lambda-go/lambda"
)

type Event struct {
    Name int `json:"name"`
}

func Handler(ctx context.Context, event Event) (string, error) {
    return fmt.Sprintf("Hello, %s!", event.Name), nil
}

func main() {
    lambda.Start(Handler)
}
```

#### **./lambda-entrypoint.sh**

```bash
#!/bin/sh

if [ $# -ne 1 ]; then
  echo "entrypoint requires the binary name to be the first argument" 1>&2
  exit 142
fi

if [ -z "${AWS_LAMBDA_RUNTIME_API}" ]; then
    exec /usr/local/bin/aws-lambda-rie entry "${PARTITION}" -- "${LAMBDA_TASK_ROOT}/$1"
else
    exec entry "${PARTITION}" -- "${LAMBDA_TASK_ROOT}/$1"
fi
```

#### **./Dockerfile**

```dockerfile
FROM alpine:3.16 AS runtime
ENV LAMBDA_RUNTIME_DIR=/var/runtime
ENV LAMBDA_TASK_ROOT=/var/task
WORKDIR ${LAMBDA_TASK_ROOT}

# Install runtime interface emulator
COPY --from=public.ecr.aws/lambda/provided:latest --chmod=755 /usr/local/bin/aws-lambda-rie /usr/local/bin/aws-lambda-rie
# Install sentential requirements
# Note: if you have problems, check that this entry semver is up to date
# https://github.com/wheegee/entry
COPY --chmod=755 --from=ghcr.io/wheegee/entry:0.4.1 / /bin/
COPY --chmod=755 lambda-entrypoint.sh /lambda-entrypoint.sh

# Set up entrypoint
ENTRYPOINT [ "/lambda-entrypoint.sh" ]

# Build stage
FROM golang:alpine3.16 AS build
WORKDIR /src
COPY ./src/go.mod ./src/go.sum ./
RUN go mod download
COPY ./src/ ./
RUN GOOS=linux go build -o app

FROM runtime AS explore

COPY --from=build /src/app .

CMD ["app"]
```

<!-- tabs:end -->

### Prepare

```bash
> cd src
> go mod init explore
> go mod tidy
> cd ..
```

### Build

```bash
> sntl build
```

### Verify

```bash
> sntl deploy local
> sntl invoke local '{"name": "explore"}'

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
  "Payload": "\"Hello, explore!\""
}
```