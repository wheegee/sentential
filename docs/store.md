# Store

Sentential uses SSM for configuration persistence. Each store is unique to its [partition](/partition).

## Args

Key value pairs stored in the `args` store will be available to the docker build at build time.

```shell
> sntl args --help
```

## Envs

Key value pairs stored in the `envs` store will be available in the lambdas environment variables and for [policy](/policy) rendering.

```shell
> sntl envs --help
```

## Secrets

Key value pairs stored in the `secrets` store will be available in the lambdas environment variables.

```shell
> sntl secrets --help
```

## Tags

Key value pairs stored in the `tags` store will be applied as tags to all taggable resources at deploy time.

```shell
> sntl tags --help
```

## Configs

Key value pairs modified in the `configs` store will be applied to the lambdas configuration at deploy time.

```shell
> sntl configs --help
```

To see documented configurations for adjustment run...

```shell
> sntl configs read
```

# Shapes

You will notice there is a file called `shapes.py` created at init time.

If you define your store schema using this file, the defined store will disallow undefined values.

This functionality is useful for defining parameters for your application. Said parameters can be defaulted, set as required or optional, as well as provides a means to document what the parameter is for.