import pytest
from sentential.lib.clients import clients

#
# Mock ECR Api Behavior
#


def get_blob(request, context):
    # all requests recieved by this mock must be of path...
    # /v2/{repo_name}/blobs/{image_digest}

    image_digest = request.path.split("/")[-1]
    repo_name = request.path.split("/")[-3]
    image_id = [{"imageDigest": image_digest}]
    clients.ecr.batch_get_images(repositoryName=repo_name, imageIds=image_id)
