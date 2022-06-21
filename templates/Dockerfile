FROM segment/chamber:2 AS chamber

FROM {{ config.runtime }} as chambered
ENV AWS_LAMBDA_EXEC_WRAPPER=/opt/wrapper.sh
COPY --from=chamber /chamber /bin/chamber
COPY --chmod=755 wrapper.sh /opt/

FROM chambered
COPY src/* ${LAMBDA_TASK_ROOT}
CMD ["app.handler"]