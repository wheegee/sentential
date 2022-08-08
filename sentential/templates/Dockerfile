FROM segment/chamber:2 AS chamber

FROM {{ runtime }} as chambered
ENV AWS_LAMBDA_EXEC_WRAPPER=/opt/wrapper.sh
COPY --from=chamber /chamber /bin/chamber
COPY --chmod=755 ./.sntl/wrapper.sh /opt/

FROM chambered
ENV repository_name={{ repository_name }}
ENV partitions=qa,prod
COPY ./src/* ${LAMBDA_TASK_ROOT}
# insert application specific build steps here
CMD ["app.handler"]
