### Mount Schedule

[EventBridge Rules](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rules.html), along with [schedule expressions](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-create-rule-schedule.html), can be used to run AWS Lambda functions on a schedule.

Sentential—via its **mount** system—provides a simple way to create an execution schedule for functions.

To demonstrate this functionality, we will write a small function to upload current weather data to S3.

### Prerequisites

You have initialized the [explore project](/examples/project) and are operating in said directory.

### Develop

Create or modify...

<!-- tabs:start -->

#### **./src/app.py**

```python
import boto3
import requests
from os import environ

MY_REGION = "us-west-2"

region = environ.get('AWS_DEFAULT_REGION', MY_REGION)
s3 = boto3.client("s3", region_name=region)

lat = "34.42"
lon = "-119.70"
url = "https://api.open-meteo.com/v1/forecast?latitude=%s&longitude=%s&current_weather=true" % (lat, lon)

def handler(event, context):
    response = requests.get(url)

    s3.put_object(
        Bucket="my_bucket",
        Key="weather.json",
        Body=response.text,
    )

```

#### **./src/requirements.txt**

```txt
requests
```

#### **./Dockerfile**

Add this `RUN` stanza to the `./Dockerfile` under the `explore` stage.

```dockerfile
RUN pip install -r requirements.txt
```

#### **./policy.json**

```json
{
    "Effect": "Allow",
    "Action": [
        "s3:PutObject"
    ],
    "Resource": "*"
}
```

<!-- tabs:end -->

### Build

```shell
> sntl build
```

### Verify

```shell
> sntl deploy local
> sntl invoke local '{}'

{
  "ResponseMetadata": {
    "HTTPStatusCode": 200,
    "HTTPHeaders": {
      "date": "Wed, 08 Mar 2023 02:04:19 GMT",
      "content-length": "4",
      "content-type": "text/plain; charset=utf-8"
    },
    "RetryAttempts": 0
  },
  "StatusCode": 200,
  "Payload": "null"
}
```

It's possible you may be running into errors at this point, perhaps surrounding region or bucket configuration. And maybe the invoke output isn't verbose enough?

Try out `sntl logs local` to dump the lambda logs directly.

### Publish & deploy

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

### Schedule

Let's schedule our function to run once every 6 hours using either of the following expressions:
- `rate(6 hours)`
- `cron(0 */6 * * ? *)`

**Note:** Single or double quotes are required around scheduling expressions.

```shell
> sntl mount schedule "rate(6 hours)"
> sntl ls

  build   arch    status   hrefs         mounts             
 ────────────────────────────────────────────────────────── 
  local   arm64            []            []                 
  0.0.2   arm64   active   ['console']   ['rate(6 hours)']  
  0.0.1   arm64            []            []
```

You will now see that one of the non-local builds has a mount of `rate(6 hours)`.

### Cleanup

```shell
> sntl destroy local
> sntl destroy aws
```
