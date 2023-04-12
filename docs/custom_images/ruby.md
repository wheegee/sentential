# Ruby

### Prerequisites

You have initialized the [explore project](/explore/project) and are operating in said directory.

### Develop

Create or modify...

<!-- tabs:start -->

#### **./src/app.rb**

```ruby
require_relative 'ruby_3_patch'

def handler(event:, context:)
    "echo: #{event}"
end
```

#### **./src/ruby_3_patch.rb**
The ruby ric is a bit behind the times. As of this documentation, this [issue](https://github.com/aws/aws-lambda-ruby-runtime-interface-client/issues/14) requires a monkeypatch.

It is possible that by the time you are reading this the problem has been resolved, and perhaps this monkeypatch is now breaking.

If this is the case please submit an Issue or PR!

```ruby
require 'aws_lambda_ric'
require 'io/console'
require 'stringio'

module AwsLambdaRuntimeInterfaceClient
  class LambdaRunner
    def send_error_response(lambda_invocation, err, exit_code = nil, runtime_loop_active = true)
      error_object = err.to_lambda_response
      @lambda_server.send_error_response(
        request_id: lambda_invocation.request_id,
        error_object: error_object,
        error: err,
        xray_cause: XRayCause.new(error_object).as_json
      )
      @exit_code = exit_code unless exit_code.nil?
      @runtime_loop_active = runtime_loop_active
    end
  end
end
```

#### **./lambda-entrypoint.sh**

```bash
#!/bin/sh

if [ $# -ne 1 ]; then
  echo "entrypoint requires the handler name to be the first argument" 1>&2
  exit 142
fi

if [ -z "${AWS_LAMBDA_RUNTIME_API}" ]; then
    exec /usr/bin/aws-lambda-rie /usr/bin/aws_lambda_ric $1
else
    exec /usr/bin/aws_lambda_ric $1
fi
```

#### **./Dockerfile**

```dockerfile
FROM alpine:3.16 AS ruby
# Install Ruby
RUN apk add --no-cache \
    ruby \
    ruby-dev

FROM ruby AS runtime
ENV LAMBDA_RUNTIME_DIR=/var/runtime
ENV LAMBDA_TASK_ROOT=/var/task
WORKDIR ${LAMBDA_TASK_ROOT}
# Install python lambda runtime interface client
RUN gem install bundler aws_lambda_ric
# Install runtime interface emulator
COPY --from=public.ecr.aws/lambda/provided:latest --chmod=755 /usr/local/bin/aws-lambda-rie /usr/bin/aws-lambda-rie
# Install sentential requirements
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