# Permissions

Lambdas allow for granting granular permissions to your function via AWS IAM [actions and conditions](https://docs.aws.amazon.com/service-authorization/latest/reference/reference_policies_actions-resources-contextkeys.html). Sententinal implements this via the `policy.json` of your project.

Sentential has the option to template key information into your policy at runtime. This is not required, but it is highly useful.

```shell
> sntl policy ls # show available templating data
> sntl policy echo # render policy to console
```

The policy rendered reprisents the policy which will be applied to your Lambda if deployed.