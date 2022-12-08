FROM runtime AS {{ repository_name }}
COPY ./src/ ${LAMBDA_TASK_ROOT}

# insert application specific build steps here

CMD ["app.handler"]
