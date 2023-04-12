# ElastiCache

This example aims to illustrate how to arrive at a basic ElastiCache setup with a Lambda.

### Prerequisites

1. You have initialized the [explore project](/explore/project).
1. You have initialized the [service infrastructure vpc](/services/vpc).

### Infrastructure

In your infrastructure directory create an `elasticache.tf` like so...

```bash
> touch elasticache.tf
> tree
.
├── elasticache.tf
└── main.tf
```

<!-- tabs:start -->

#### **./main.tf**

This should already be populated from the [prerequisite step]((/services/vpc)).

#### **./elasticache.tf**

```hcl
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "explore"
  engine               = "redis"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  engine_version       = "7.0"
  port                 = 6379
  subnet_group_name    = module.vpc.elasticache_subnet_group_name
  security_group_ids   = [aws_security_group.allow_self.id]
}

output "redis_host" {
  value = aws_elasticache_cluster.redis.cache_nodes[0].address
}
```

<!-- tabs:end -->

### Develop

For this example we are going to simply validate the structure of an event. We will throw a validation error on failure, and return the event if it's valid.

<!-- tabs:start -->

#### **./src/app.py**

```python
from redis import StrictRedis
from redis_cache import RedisCache
from pydantic import BaseModel

#
# ElastiCache
#

if os.environ.get("HOSTNAME") != "sentential":
     print("establishing connection to elasticache redis...")
     client = StrictRedis(host=os.environ.get("REDIS_HOST"))
else:
     print("establising connection to host.docker.internal redis...")
     client = StrictRedis(host="host.docker.internal")

cache = RedisCache(redis_client=client)

#
# Input/Output Models
#

class Event(BaseModel):
     version: str
     dimension: int

def proxy(event, context):
     print(f"event: {event}")     
     return handler(event)

@cache.cache()
def handler(event):
     print("event not cached, running handler...")
     validated_event = Event(**event)
     return validated_event.dict()
```

#### **./src/requirements.txt**

```txt
pydantic
redis
python-redis-cache
```

#### **./Dockerfile**

Add this `RUN` stanza to the `./Dockerfile` under the `explore` stage.

```dockerfile
RUN pip install -r requirements.txt
```

And modify the `CMD` stanza to be

```dockerfile
CMD ["app.proxy"]
```

<!-- tabs:end -->

### Configure

In order for our Lambda to be able to reach our ElastiCache instance in our private subnet, we need to add some configurations.

Note that this information is output by our Terraform.

```bash
> sntl configs set security_group_ids '["sg-...", "sg-..."]'
> sntl configs set subnet_ids '["sn-...", "sn-..."]'
> sntl envs set REDIS_HOST <hostname>
```

### Validate

Since ElastiCache is best left secured within a private subnet, we don't have access to it from our local environment. So let's create a local Redis instance for our Lambda to use...

```bash
> docker run --name sentential-redis -p 6379:6379 -d redis
```

Now we can move on to our usual validation flow...

```bash
> sntl build
> sntl deploy local
> sntl invoke local '{}' 
# => results in validation error
> sntl invoke local '{ "version": "0.0.1", "dimension": 0 }'
# => note that the function logs that it ran the handler
> sntl invoke local '{ "version": "0.0.1", "dimension": 0 }'
# => note that the function does not log that it ran the handler
```

### Deploy

```bash
> sntl publish
> sntl deploy aws
> sntl invoke aws '{}' 
# => results in validation error
> sntl invoke aws '{ "version": "0.0.1", "dimension": 0 }'
# => note that the function logs that it ran the handler
> sntl invoke aws '{ "version": "0.0.1", "dimension": 0 }'
# => note that the function does not log that it ran the handler
```

### Cleanup

```bash
> sntl destroy local
> sntl destroy aws
> docker rm -f sentential-redis
```
