# RDS

This example aims to illustrate how to arrive at a basic RDS setup with a Lambda.

### Prerequisites

1. You have initialized the [explore project](/explore/project).
1. You have initialized the [service infrastructure vpc](/services/vpc).

### Infrastructure

In your infrastructure directory create an `rds.tf` like so...

```bash
> touch rds.tf
> tree
.
├── rds.tf
└── main.tf
```

<!-- tabs:start -->

#### **./main.tf**

This should already be populated from the [prerequisite step]((/services/vpc)).

#### **./rds.tf**

> :lock: best practice deams you should
> 1. Not allow secrets to enter your terraform state.
> 2. Not use static credentials for RDS access.
>
> See the [further reading](/services/rds?id=further-reading) section for more.

```hcl
locals {
    name    = "rds-explore-proxy"
    db_user = "throwaway"
    db_pass = "throwaway"
}

resource "aws_db_instance" "rds" {
  allocated_storage    = 10
  db_name              = "explore"
  engine               = "postgres"
  engine_version       = "14.6"
  instance_class       = "db.t3.micro"
  username             = local.db_user
  password             = local.db_pass
  
  publicly_accessible                 = false
  skip_final_snapshot                 = true
  iam_database_authentication_enabled = true
  
  db_subnet_group_name   = module.vpc.database_subnet_group_name
  vpc_security_group_ids = [aws_security_group.allow_self.id]
}

module "rds_proxy" {
  source = "terraform-aws-modules/rds-proxy/aws"

  create_proxy = true
  iam_auth     = "DISABLED"

  name                   = local.name
  iam_role_name          = local.name
  vpc_subnet_ids         = module.vpc.private_subnets
  vpc_security_group_ids = [aws_security_group.allow_self.id]

  db_proxy_endpoints = {
    read_write = {
      name                   = "read-write-endpoint"
      vpc_subnet_ids         = module.vpc.private_subnets
      vpc_security_group_ids = [aws_security_group.allow_self.id]
      tags                   = local.tags
    }
  }

  secrets = {
    (local.db_user) = {
      description = aws_secretsmanager_secret.superuser.description
      arn         = aws_secretsmanager_secret.superuser.arn
      kms_key_id  = aws_secretsmanager_secret.superuser.kms_key_id
    }
  }

  engine_family = "POSTGRESQL"
  debug_logging = true

  # Target RDS instance
  target_db_instance     = true
  db_instance_identifier = aws_db_instance.rds.id

  tags = local.tags
}

data "aws_kms_alias" "secretsmanager" {
  name = "alias/aws/secretsmanager"
}

resource "aws_secretsmanager_secret" "superuser" {
  name        = "${local.db_user}-1"
  description = "${aws_db_instance.rds.db_name} RDS super user credentials"
  kms_key_id  = data.aws_kms_alias.secretsmanager.id
  
  tags = local.tags
}

#
# This should be done by hand in a real scenario to prevent secret from entering TF state
#

resource "aws_secretsmanager_secret_version" "superuser" {
  secret_id = aws_secretsmanager_secret.superuser.id
  secret_string = jsonencode({
    username = local.db_user
    password = local.db_pass
  })
}

output "rds_host" {
    value = module.rds_proxy.proxy_endpoint
}

output "rds_user" {
    value = local.db_user
}

output "rds_pass" {
    value = local.db_pass
}
```

<!-- tabs:end -->

### Develop

For this example, we are going to connect to our RDS instance via the RDS Proxy and get the current time.

<!-- tabs:start -->

#### **./src/app.py**

```python
import psycopg2
import os

ENDPOINT=os.getenv("RDS_HOST")
USER=os.getenv("RDS_USER")
PASS=os.getenv("RDS_PASS")
PORT="5432"
DBNAME="explore"

if os.environ.get("HOSTNAME") != "sentential":
     print("establishing connection to RDS proxy...")
     conn = psycopg2.connect(host=ENDPOINT, port=PORT, database=DBNAME, user=USER, password=PASS, sslmode='require')
else:
     print("establising connection to host.docker.internal...")
     conn = psycopg2.connect(host="host.docker.internal", port=PORT, database=DBNAME,  user=USER, password=PASS)

def handler(event, context):
     try:
          print("connecting...")
          cur = conn.cursor()
          cur.execute("""SELECT now()""")
          query_results = cur.fetchall()
          res = { "result": f"{query_results}" }
          print(res)
          return res
     except Exception as e:
          print("Database connection failed due to {}".format(e))
```

#### **./src/requirements.txt**

```txt
aws-psycopg2
boto3
```

#### **./Dockerfile**

Add this `RUN` stanza to the `./Dockerfile` under the `explore` stage.

```dockerfile
RUN pip install -r requirements.txt
```

<!-- tabs:end -->

### Configure

In order for our Lambda to be able to reach our RDS Proxy in our private subnet, we need to add some configurations.

Note that this information is output by our terraform.

```bash
> sntl configs write security_group_ids '["<tf_output_1>", ..., "<tf_output_n>"]'
> sntl configs write subnet_ids '["<tf_output_1>", ..., "<tf_output_n>"]'
> sntl envs write RDS_HOST <tf_output>
> sntl envs write RDS_USER <tf_output>
> sntl envs write RDS_PASS <tf_output>
```

> :people_hugging: The interface for passing arrays to the `configs` store is cludgy and tempermental. Follow the exact formatting as above, improvements will be made.

### Validate

Since RDS is best left secured within a private subnet, we don't have access to it from our local environment. So let's create a local Postgres instance for our Lambda to use...

```bash
docker run --name sentential-postgres \
           -p 5432:5432 \
           -e POSTGRES_USER=throwaway \
           -e POSTGRES_PASSWORD=throwaway \
           -e POSTGRES_DB=explore \
           -d postgres
```

Now we can move on to our usual validation flow...

```bash
> sntl build
> sntl deploy local
> sntl invoke local '{}' 
{
  "ResponseMetadata": {
    "HTTPStatusCode": 200,
    "HTTPHeaders": {
      "date": "Tue, 28 Feb 2023 16:46:43 GMT",
      "content-length": "99",
      "content-type": "text/plain; charset=utf-8"
    },
    "RetryAttempts": 0
  },
  "StatusCode": 200,
  "Payload": "{\"result\": \"[(datetime.datetime(2023, 2, 28, 16, 25, 27, 134598, tzinfo=datetime.timezone.utc),)]\"}"
}
```

### Deploy

```bash
> sntl publish
> sntl deploy aws
> sntl invoke aws '{}' 
# this should return a similar response to the local invocation
```

### Cleanup

```bash
> sntl destroy local
> sntl destroy aws
> docker rm -f sentential-postgres
```

### Further reading

- [Terraform State & Secrets](https://developer.hashicorp.com/terraform/language/state/sensitive-data)
- [IAM RDS connections](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/UsingWithRDS.IAMDBAuth.html)
- [IAM RDS Proxy connections](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/rds-proxy-setup.html#rds-proxy-connecting-iam)
