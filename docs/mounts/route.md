# Route

[API Gateway](https://docs.aws.amazon.com/apigateway/index.html) can be used to create publicly accessible https routes by which to invoke your http based lambdas.

Sentential—via its **mount** system—provides a simple way to create an API Gateway integration for functions and mount said integration to an API route.

To demonstrate this functionality, we will write a small function to inspect our http request headers.

### Prerequisites

You have initialized the [explore project](/examples/project?id=explore-project-setup) and are operating in said directory.

### Develop

Create or modify...

<!-- tabs:start -->

#### **./src/app.py**

```python
from fastapi import FastAPI, Request
from mangum import Mangum

app = FastAPI()

@app.get("/")
def request_headers(request: Request):
    return request.headers

handler = Mangum(app, lifespan="off")
```

#### **./src/requirements.txt**

```txt
fastapi
mangum
```

#### **./Dockerfile**

Add this `RUN` stanza to the `./Dockerfile` under the `explore` stage.

```dockerfile
RUN pip install -r requirements.txt
```

<!-- tabs:end -->

### Build

```shell
> sntl build
```

### Verify

```shell
> sntl deploy local --public-url
> sntl invoke local '{}'
> curl localhost:8999

{
  "accept":"*/*",
  "user-agent":"curl/7.81.0"
}
```

### Publish & Deploy

```shell
> sntl publish
> sntl deploy aws
> sntl ls

  build   arch    status   hrefs         mounts  
 ─────────────────────────────────────────────── 
  local   arm64   running  []            []      
  0.0.2   arm64   active   ['console']   []      
  0.0.1   arm64            []            []  
```

### Mount Route

This step assumes you already have at least one [HTTP API Gateway](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api.html) launched in your AWS account.

```shell
> sntl mount route [tab][tab] # use tab to discover/autocomplete available gateway urls
> sntl mount route {api_id}.execute-api.us-west-2.amazonaws.com
> sntl ls

  build   arch    status   hrefs         mounts             
 ────────────────────────────────────────────────────────── 
  local   arm64            []            []                 
  0.0.2   arm64   active   ['console']   ['/']  
  0.0.1   arm64            []            []
```

Visit the gateway url in your browser.

> :information_source:
> Within the headers of the request you will find the `X-Forwarded-Prefix`. This will contain the route under which the lambda is mounted.
> It is useful to have this in concert with the `host` header so you application can properly handle redirects etc.

### Cleanup

```shell
> sntl destroy local
> sntl destroy aws
```

### Further reading

- [mangum](https://mangum.io/)
- [lamby](https://lamby.custominktech.com/)
- [serverless-express](https://github.com/vendia/serverless-express)