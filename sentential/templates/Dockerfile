FROM {{ runtime }} AS runtime
ENV AWS_LAMBDA_EXEC_WRAPPER=/bin/wrapper.sh
COPY --chmod=755 --from=ghcr.io/linecard/entry:{{ entry_version }} / /bin/

FROM runtime AS {{ repository_name }}
COPY ./src/ ${LAMBDA_TASK_ROOT}

# insert application specific build steps here

CMD ["app.handler"]
