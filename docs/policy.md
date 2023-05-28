# Policy

Lambdas allow for granting granular permissions to your function via AWS IAM [actions and conditions](https://docs.aws.amazon.com/service-authorization/latest/reference/reference_policies_actions-resources-contextkeys.html). Sententinal implements this via the `policy.json` of your project.

The `policy.json` document is applied to both your locally deployed lambda, and your AWS deployed lambda.

Sentential has the option to template key information into your policy at runtime. This is not required, but it is highly useful.

## Interpolation Data

Data from evaluated `context` as well as any unencrypted [store](/store) information is available at policy rendering time for interpolation.

To see what information is available to interpolate into your policy document, run...

```shell
> sntl policy ls
```

## Interpolation Result

To verify your policy is rendering to what you expect, run...

```shell
> sntl policy cat
```