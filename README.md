# Missing Bits
- configuration of ecr registry (to be documented and manually created)
- configuration of ssm secrets (to be documented and manually created)

# Moving parts
- `ops/local` - tf apply brings up local lambda
- `ops/aws` - tf apply brings up aws lambda + url
- `kaixo/src` - `python3 main.py` runs server locally 