# Build

```bash
> sntl build
```

## Moving Parts

### Dockerfile

If you inspect the generated `Dockerfile` after project initialization, you will notice it is a multistage build. This is so that Sentential can utilize [entry](https://github.com/linecard/entry), enabling Sentential to manage your Lambda's Environment Variables and Secrets. You can simply remove this and it will result in Sentential conventions no longer working, but your image will still be Lambda compatible.

The build follows all conventions set by AWS. The `CMD` stanza should be a dot notated path to the handler you wish to be exucted in your source. 

### Build Args

If you need to pass build time arguments to your image build, you can use the `sntl args` ssm store to define said parameters.

If you want to strictly type and define your build arguments for future generations to understand, use `shapes.py`.