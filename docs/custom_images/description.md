# Custom images

By default, Sentential templates an [AWS maintained base image](https://gallery.ecr.aws/lambda?page=1) into your `./Dockerfile` at `init` time. For the most part, these images do the job.

However, there are reasons to use your own desired distribution. For example, your organization might require you to only build off of internally maintained base Docker images. Or perhaps you are really leet and you refuse to use anything other than Arch. Whatever the case may be, this guide aims to help you on your way.

Note that nothing in these document are particular to Sentential. But Sentential does make it easier to go about experimenting with building your own custom Lambda Docker images.

### Further reading

- [custom runtime docs](https://docs.aws.amazon.com/lambda/latest/dg/runtimes-walkthrough.html)
- [runtime interface clients](https://docs.aws.amazon.com/lambda/latest/dg/runtimes-images.html#runtimes-api-client)
- [runtime interface emulator](https://github.com/aws/aws-lambda-runtime-interface-emulator)
