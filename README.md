# Missing Bits
to be documented for manual creation once...
- configuration of ecr registry
- configuration of ssm secrets
- configuration of shared tf state for aws deployments
to be fixed up...
- utilize `ops/common/lib/mock_role.sh` to generate local credentials instead of passing `~/.aws/credentials`
- generalize the api dir from `kaixo` to something less specific.
- ...?

# Moving parts
- `ops/local` - tf apply brings up local lambda
- `ops/aws` - tf apply brings up aws lambda + url
- `kaixo/src` - `python3 main.py` runs server locally