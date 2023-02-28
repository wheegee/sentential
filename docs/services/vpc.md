## Services VPC Setup

For the examples in this section, you will need a VPC. The below VPC setup using [terraform](https://www.terraform.io/) is a minimized configuration to illuminate the requirements of the examples. These requirements can be overlayed onto whatever setup, using whatever IaC.

### infrastructure
Create a folder somewhere reasonable for infrastructure code and populate it like so...

```shell
> tree
.
└── main.tf
```

<!-- tabs:start -->

#### **./main.tf**

> :money_with_wings: In order to keep costs at a minimum, the vpc is created without NAT gateways, which means your private subnets do not have internet access.

```hcl
locals {
  tags = {
    Terraform = "true"
    Environment = "explore"
  }
}

module "vpc" {
  source = "terraform-aws-modules/vpc/aws"

  name = "explore"
  cidr = "10.0.0.0/16"

  azs             = ["us-west-2a", "us-west-2b", "us-west-2c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
  elasticache_subnets = ["10.0.104.0/24", "10.0.105.0/24", "10.0.106.0/24"]
  database_subnets = ["10.0.107.0/24", "10.0.108.0/24", "10.0.109.0/24"]
  
  enable_nat_gateway = false
  single_nat_gateway = false
  one_nat_gateway_per_az = false

  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = local.tags
}

resource "aws_security_group" "allow_self" {
  name        = "explore_self"
  description = "Allow all traffic between members"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description      = "Allow all ingress from members"
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = [module.vpc.vpc_cidr_block]
  }

  egress {
    description      = "Allow all egress to anywhere"
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = local.tags
}

module "endpoints" {
  source = "terraform-aws-modules/vpc/aws//modules/vpc-endpoints"

  vpc_id             = module.vpc.vpc_id
  security_group_ids = [aws_security_group.allow_self.id]

  endpoints = {
    s3 = {
      service             = "s3"
      tags                = { Name = "s3-vpc-endpoint" }
    },
    ssm = {
      service             = "ssm"
      private_dns_enabled = true
      subnet_ids          = module.vpc.private_subnets
    },
    lambda = {
      service             = "lambda"
      private_dns_enabled = true
      subnet_ids          = module.vpc.private_subnets
    },
    kms = {
      service             = "kms"
      private_dns_enabled = true
      subnet_ids          = module.vpc.private_subnets
    },
    logs = {
        service = "logs"
        private_dns_enabled = true
        subnet_ids = module.vpc.private_subnets
    }
  }

  tags = local.tags
}

output "subnet_ids" {
  value = module.vpc.private_subnets
}

output "security_group_ids" {
  value = [aws_security_group.allow_self.id]
}
```

<!-- tabs:end -->