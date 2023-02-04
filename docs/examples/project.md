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
If you look in the `Dockerfile` you will see a multi-stage build setup. In general, all your application build steps will be within the `FROM runtime AS explore` stanza. The rest of the multi-stage build represent a pattern. These can be modified to do things like build custom runtime containers from `alpine`, `arch` or whatever distro you prefer. However, as-is configuration is generally sufficient and you can go a very long way with it.

### policy.json
Every lambda must have a policy associated with it which allows said lambda to be invoked. On top of this, it the policy is responsible for providing a lambda with access to AWS resources. Sentential templates this policy.json at deploy time. You can simply write your policy as a static entity, or you can template in information from your lambdas environment or contextual information (such as account id, region, and a host of other data made available by Sentential). 

### shapes.py
Sentential implements an optional concept of shapes to put contracts and expectations on a given projects resource tagging, runtime environment, variables, and build arguments. It is not necessary to use this file. But it does provide a powerful layer to clarify operational requirements to end users of your project. For example it can allow you to express things like "in order to deploy this lambda you must provide S3_BUCKET_NAME". To harken back to policy.json, `S3_BUCKET_NAME` would then be assuredly available to policy.json for templating in access permissions for such a concept. 

