FROM amazon/aws-lambda-python

ADD requirements.txt /${LAMBDA_TASK_ROOT}/requirements.txt
RUN pip install -r requirements.txt

ADD src/ ${LAMBDA_TASK_ROOT}
ENV API_NAME=kaixo
ENV API_VERSION=0.0.1
ENV API_DESCRIPTION="test api"

CMD ["main.handler"]
