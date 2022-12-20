from os import environ


def handler(event, context):
    return dict(environ)
