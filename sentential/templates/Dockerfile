
FROM segment/chamber:2 AS chamber

FROM {{ runtime }} AS chambered
ENV AWS_LAMBDA_EXEC_WRAPPER=/opt/wrapper.sh
COPY --from=chamber /chamber /bin/chamber
RUN echo '#!/bin/bash' > /opt/wrapper.sh
RUN echo 'chamber exec $PARTITION -- $@' >> /opt/wrapper.sh
RUN chmod 755 /opt/wrapper.sh

FROM chambered
ENV repository_name={{ repository_name }}
ENV partitions=qa,prod
COPY ./src/* ${LAMBDA_TASK_ROOT}
# insert application specific build steps here
CMD ["app.handler"]
