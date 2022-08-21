FROM {{ runtime }} AS runtime
ARG TARGETARCH
ENV AWS_LAMBDA_EXEC_WRAPPER=/opt/wrapper.sh
ADD https://github.com/wheegee/sentential-entry/releases/latest/download/sentry-${TARGETARCH} /bin/sentry
RUN echo '#!/bin/bash' > /opt/wrapper.sh
RUN echo 'sentry env $PARTITION -- $@' >> /opt/wrapper.sh
RUN chmod 755 /bin/sentry /opt/wrapper.sh

FROM runtime AS {{ repository_name }}
COPY ./src/* ${LAMBDA_TASK_ROOT}

# insert application specific build steps here

CMD ["app.handler"]
