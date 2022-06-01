FROM amazon/aws-lambda-python

ADD requirements.txt /${LAMBDA_TASK_ROOT}/requirements.txt
RUN pip install -r requirements.txt

ADD src/ ${LAMBDA_TASK_ROOT}

ENV API_NAME=${API_NAME}
ENV API_VERSION=${API_VERSION}
ENV API_DESCRIPTION=${API_DESCRIPTION}

CMD ["main.handler"]
