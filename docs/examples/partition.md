## Partition
You may already be asking yourself: "how do I deploy more than one lambda?"

Enter `PARTITION`.

Everything you have been constructing using Sentential thus far has been using a default `PARTITION` equal to your AWS User ID. This convention is handy, because it automatically gives you a unique namespace for you to operate within. In general this namespace can be thought of as `/${PARTITION}/${PROJECT}/*`. This changes a bit depending on the type of resource you are creating and the naming patterns they allow. For example a lambda would be created with `${PARTITION}-${PROJECT}` because lambdas cannot have `/` in their names.

In this document we are going to briefly explore the behavior of `PARTITION`; you can read more in the [core docs](https://github.com/wheegee/sentential/wiki/Core).

> :warning: This document describes a key configuration for Sentential which is camping on the environment variable `PARTITION`. I say "camping" because `PARTITION` is a really useful environment variable for a lot of different applications. We will be changing this in the near future to something more wise like `SNTL_ENV`.

### prerequisites
you have initialized the [explore project](/examples/project) and are operating in said directory.

### scenario
Our development team has convinced product that we have to fix some tech debt. Across our code base is a plethora of string-to-uppercase method implementations. Instead of using STDLIB or a shared library, we have decided to go cloud native with a microservice to uppercase strings, replacing the old-school approaches with a more modern and convenient POST request. We are deciding between naming it after a Lord Of The Rings character or just picking a random word and removing a few letters (`sntl`?). That's not blocking though, so let's get to work.

### develop

Create or modify...

<!-- tabs:start -->

#### **./src/app.py**

```python
# src/app.py
def handler(event, context):
     return upper(event["str"])
```

<!-- tabs:end -->


### verify
```shell
> sntl build
> sntl deploy local
> sntl invoke local '{ "str": "what?" }'
```

This returns the expected output. You really are a Rockstar. This thing is bullet proof. Probably doesn't even need QA'ing, but let's just make it easily available so we can move the card to the correct swimlane and get some of that gamification dopamine.

### publish
```shell
> sntl publish
> PARTITION=qa sntl deploy aws
```

### share
Since we want to share this masterpiece with QA, let's just give them the `PARTITION` name `qa` to go have a look.

Shell of qa engineer:
```shell
PARTITION=qa sntl invoke aws '{ "str": "ought to be upper" }'
# output contains "OUGHT TO BE UPPER"... looking good
sntl invoke aws '{ "str": 123 }'
```

And scene...

### cleanup

```shell
> sntl destroy local
> PARTITION=qa sntl destroy aws
```