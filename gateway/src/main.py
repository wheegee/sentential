import uvicorn
import boto3
import json
import os
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Route
from models.api_gateway_v2 import (
    APIGatewayV2Event,
    APIGatewayV2Response,
    RequestContextStruct,
    HttpStruct
)

client = boto3.client(
    'lambda',
    region_name=os.getenv("AWS_REGION", default="us-west-2"),
    endpoint_url=os.getenv("LAMBDA_ENDPOINT", "http://localhost:9000")
)


async def proxy(request):
    # import code; code.interact(local=dict(globals(), **locals()))

    event = APIGatewayV2Event(
        raw_path=request.url.path,
        raw_query_string=request.url.query,
        cookies=[f"{key}={value}" for (key, value) in request.cookies.items()],
        headers=request.headers,
        query_string_parameters=request.query_params,
        path_parameters=request.path_params,
        request_context=RequestContextStruct(
            http=HttpStruct(
                method=request.method,
                path=request.url.path,
                source_ip=request.client.host
            )
        ),
        body=await request.body()
    )

    lambda_response = client.invoke(
        FunctionName='function',
        LogType='Tail',
        Payload=event.json(by_alias=True, exclude_none=True),
    )

    import code; code.interact(local=locals())
    response = json.loads(lambda_response['Payload'].read())
    response = APIGatewayV2Response.parse_obj(response)
    response = Response(
        response.body,
        status_code=response.status_code,
        headers=response.headers
    )
    return response

# The "rest_of_path" thing can allow for /#{function_name}/#{rest_of_path}
# for routing to many functions if we like.
app = Starlette(
    routes=[Route(
        "/{rest_of_path:path}",
        endpoint=proxy,
        methods=["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    )]
)

if __name__ == '__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=8081, reload=True)
