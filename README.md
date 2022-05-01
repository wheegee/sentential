# Missing Bits
to be documented for manual creation once...
- configuration of ecr registry
- configuration of ssm secrets
- configuration of shared tf state for aws deployments

# Moving parts
- `ops/local` - tf apply brings up local lambda
- `ops/aws` - tf apply brings up aws lambda + url
- `kaixo/src` - `python3 main.py` runs server locally