FROM {{ runtime }} AS runtime
ARG TARGETARCH
ENV AWS_LAMBDA_EXEC_WRAPPER=/opt/wrapper.sh
ADD https://github.com/wheegee/sentential-entry/releases/latest/download/entry-${TARGETARCH} /bin/entry
RUN echo '#!/bin/bash' > /opt/wrapper.sh
RUN echo 'entry $PARTITION -- $@' >> /opt/wrapper.sh
RUN chmod 755 /bin/entry /opt/wrapper.sh

FROM runtime AS {{ repository_name }}
COPY ./src/ ${LAMBDA_TASK_ROOT}

# insert application specific build steps here

CMD ["app.handler"]
