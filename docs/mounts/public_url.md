# Function URL

[Function URLs](https://docs.aws.amazon.com/lambda/latest/dg/lambda-urls.html) are a very useful feature of AWS Lambda.

Sentential exposes a simple way to deploy HTTP based Lambdas both locally and on AWS via this mechanism

To demonstrate deploying an HTTP based Lambda, we are going to use the python framework FastAPI. As an example, let's implement a "what is my IP?" service.

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
def requestor_ip(request: Request):
    return request.client.host

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

```bash
> sntl build
```

### Verify

Since this is an HTTP-based Lambda, let's use the `--public-url` option when deploying our image locally.

```bash
> sntl deploy local --public-url
> sntl ls

  build   arch    status    hrefs           
 ────────────────────────────────────────── 
  local   amd64   running   ['public_url']  
  0.0.3   amd64             []              
  0.0.2   amd64             []              
  0.0.1   amd64             [] 
```

The href for public_url in the `local` build row will take you to the local endpoint in your browser. By default this is `http://localhost:8999`.

### Publish

```bash
> sntl publish
```

### Deploy

```bash
> sntl deploy aws --public-url
> sntl ls

  build   arch    status    hrefs                      
 ───────────────────────────────────────────────────── 
  local   amd64   running   ['public_url']             
  0.0.4   amd64   active    ['console', 'public_url']  
  0.0.3   amd64             []                         
  0.0.2   amd64             []                         
  0.0.1   amd64             []
```

You will now see that one of the non-local builds has a status of `active`. It has two hrefs, one to take you to the AWS webconsole for the Lambda, and another to take you to the public_url endpoint

### Cleanup

```bash
> sntl destroy local
> sntl destroy aws
```

### Further reading

- [mangum](https://mangum.io/)
- [lamby](https://lamby.custominktech.com/)
- [serverless-express](https://github.com/vendia/serverless-express)
