# Example Project Setup
We will use a project named `explore` to cover the usage and features of Sentential.

### ECR
Create an ECR repository called `explore`. 

### Init
1. `mkdir explore`
1. `cd explore`
1. `sntl init explore python`

```bash
> tree
.
├── Dockerfile
├── policy.json
├── shapes.py
└── src
```

At this point you can move on to the rest of the examples.

## Generated Files

### Dockerfile
The docker is a multi-stage build, with the `runtime` stanza being the operative location to define your application build.

### policy.json
The policy file is a templated permissions document that defines what your lambda is capable of doing in AWS. As long as your user is able to self-assume role, or generate federated tokens, local lambdas will be provisioned temporary credentials constrained to this policy.

### shapes.py
Shapes are an optional confguration to allow defining deploy-time requirements in an expressive and enforcable manner. If your projects require certain tags, environment variables, or build arguments, shapes can give you the ability to apply a self documenting schema to said operator concerns.

