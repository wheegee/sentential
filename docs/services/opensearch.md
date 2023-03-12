## OpenSearch

This example aims to illustrate how to arrive at a basic OpenSearch setup with a lambda.

### prerequisites
1. you have initialized the [explore project](/explore/project).
1. you have initialized the [service infrastructure vpc](/services/vpc).

### infrastructure
In your infrastructure directory create an `opensearch.tf` like so...

```shell
> touch opensearch.tf
> tree
.
├── opensearch.tf
└── main.tf
```

<!-- tabs:start -->

#### **./main.tf**

This should already be populated from the [prerequisite step]((/services/vpc)).

#### **./opensearch.tf**

```hcl
locals {
    domain_name = "explore"
}

resource "aws_iam_service_linked_role" "explore" {
  aws_service_name = "opensearchservice.amazonaws.com"
}

resource "aws_opensearch_domain" "explore" {
  depends_on = [aws_iam_service_linked_role.explore]
  domain_name    = "explore"
  engine_version = "OpenSearch_2.5"

  cluster_config {
    instance_type = "t3.small.search"
    zone_awareness_enabled = false
  }

  vpc_options {
    subnet_ids = [module.vpc.private_subnets[0]]
    security_group_ids = [aws_security_group.allow_self.id]
  }

  ebs_options {
    ebs_enabled = true
    volume_size = 10
  }

  access_policies = jsonencode({
    Version = "2012-10-17",
    Statement = [
        {
            Effect = "Allow"
            Principal = {
                AWS: "*"
            }
            Action = "es:*"
            Resource = "arn:aws:es:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:domain/${local.domain_name}/*"
        }
    ]
  })
  tags = local.tags
}

output "opensearch_subnet_id" {
    value = module.vpc.private_subnets[0]
}

output "opensearch_domain_endpoint" {
    value = aws_opensearch_domain.explore.endpoint
}
```

<!-- tabs:end -->

## develop

For this example we are going use the `_cat` endpoint to list our current indices.

<!-- tabs:start -->

#### **./src/app.py**

```python
import boto3
import os
from opensearchpy import OpenSearch, AWSV4SignerAuth, RequestsHttpConnection

if os.environ.get("HOSTNAME") != "sentential":
    print("establishing connection to opensearch...")
    host = os.environ.get("OPENSEARCH_HOST")
    credentials = boto3.Session().get_credentials()
    http_auth = AWSV4SignerAuth(credentials, 'us-west-2')
else:
    print("establising connection to host.docker.internal opensearch...")
    hosts='host.docker.internal'
    http_auth="admin:admin"

client = OpenSearch(    
          hosts=host,
          http_compress=True,
          http_auth=auth,
          use_ssl=True,
          verify_certs=False,
          ssl_assert_hostname=False,
          ssl_show_warn=False,
          connection_class=RequestsHttpConnection
     )

def handler(event, context):
    return client.cat.indices()
```

#### **./src/requirements.txt**

```txt
boto3
opensearch-py
```

#### **./Dockerfile**

Add this `RUN` stanza to the `./Dockerfile` under the `explore` stage.

```dockerfile
RUN pip install -r requirements.txt
```

<!-- tabs:end -->

### configure

In order for our lambda to be able to reach our Elasticache instance in our private subnet, we need to add some configurations.

Note that this information is output by our terraform.

```shell
> sntl configs write security_group_ids '["<tf_output_1>", ..., "<tf_output_n>"]'
> sntl configs write subnet_ids '["<tf_output_1>", ..., "<tf_output_n>"]' # note: this will be the opensearch_subnet_id in the terraform output.
> sntl envs write OPENSEARCH_HOST <tf_output>
```

> :people_hugging: The interface for passing arrays to the `configs` store is cludgy and tempermental. Follow the exact formatting as above, improvements will be made.


### validate

Since our opensearch cluster is going to be inside a private subnet, we will need a local opensearch instance to develop against...

```shell
> docker run -p 9200:9200 -p 9600:9600 -e "discovery.type=single-node" --name sentential-opensearch -d opensearchproject/opensearch:latest
```

Now we can move on to our usual validation flow...

```shell
> sntl build
> sntl deploy local
> sntl invoke local '{}' 
# => returns indices
```

### deploy

```shell
> sntl publish
> sntl deploy aws
> sntl invoke aws '{}' 
# => returns indices
```

### cleanup

```shell
> sntl destroy local
> sntl destroy aws
> docker rm -f sentential-opensearch
```