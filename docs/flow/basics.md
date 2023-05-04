# Flow

This section aims to highlight the flow of developing with Sentential at a high level. The pattern Sentential operates on can be visualized like so...

```mermaid
flowchart LR
  develop([<a href='/#/flow/develop'>develop</a>])
  build([<a href='/#/flow/build'>build</a>])
  verify([<a href='/#/flow/deploy'>verify</a>])
  publish([<a href='/#/flow/publish'>publish</a>])
  deploy([<a href='/#/flow/deploy'>deploy</a>])

  develop --> build --> verify --> publish --> deploy --> develop

  style develop fill: none
  style build fill: none
  style verify fill: none
  style publish fill: none
  style deploy fill: none
```

## Develop

Sentential assumes your source code to be in the `./src` dir in the root of your project. This is a convention, and is changed in no special fashion.

## Build

Sentential builds `./src` into your ECR image. What your build consists of is up to you, defined in the `Dockerfile`.

## Verify

Sentential allows you to locally deploy a lambda for verification, this includes IAM permissions parity and Environment Variable parity.

## Publish

Sentential is opinionated on semver and publishes builds to ECR.

## Deploy

Sentential deploys to AWS in a simple manner, due to what you have defined and verified above.


