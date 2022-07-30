FROM segment/chamber:2 AS chamber

FROM {{ facts.runtime }} as chambered
ENV AWS_LAMBDA_EXEC_WRAPPER=/opt/wrapper.sh
COPY --from=chamber /chamber /bin/chamber
COPY --chmod=755 {{ facts.path.wrapper }} /opt/

FROM chambered
COPY {{ facts.path.src }}/* ${LAMBDA_TASK_ROOT}
CMD ["app.handler"]