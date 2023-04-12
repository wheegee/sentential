# Permissions

Lambdas allow for granting granular permissions to your function via AWS IAM [actions and conditions](https://docs.aws.amazon.com/service-authorization/latest/reference/reference_policies_actions-resources-contextkeys.html). Sententinal implements this via the `policy.json` of your project. To exercise this, let's create a Lambda which returns a list of all S3 buckets in our current AWS account.

### Prerequisites

You have initialized the [explore project](/explore/project) and are operating in said directory.

### Develop

Create or modify...

<!-- tabs:start -->

#### **./src/app.py**

```python
import boto3
from os import environ

MY_REGION = "us-west-2"

region = environ.get('AWS_DEFAULT_REGION', MY_REGION)
s3 = boto3.client("s3", region_name=region)

def handler(event, context):
     buckets = s3.list_buckets()['Buckets']
     return [ bucket['Name'] for bucket in buckets ]
```

#### **./src/requirements.txt**

```txt
boto3
```

#### **./Dockerfile**

Add this `RUN` stanza to the `./Dockerfile` under the `explore` stage.

```dockerfile
RUN pip install -r requirements.txt
```

#### **./policy.json**

Inject this new policy statement along with the others.

```json
{
    "Effect": "Allow",
    "Action": [
        "s3:GetBucketLocation",
        "s3:ListAllMyBuckets"
    ],
    "Resource": "*"
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
  "Payload": "[bucket-name-1, bucket-name-2, ..., bucket-name-n]"
}
```

It's possible you may be running into errors at this point, perhaps surrounding region configuration. And maybe the invoke output isn't verbose enough?

Try out `sntl logs local` to dump the Lambda logs directly.

### Publish & deploy

Publishing and deploying to AWS can be an exercise for the reader at this point.

### cleanup
```bash
> sntl destroy local
```
