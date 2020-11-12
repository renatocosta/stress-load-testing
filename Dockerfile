FROM python:3.8.5-alpine3.12
ENV PYTHONPATH /locustfiles

COPY requirements.txt requirements.txt
RUN apk --no-cache add --virtual=.build-dep \
      build-base \
    && apk --no-cache add bash libzmq libffi-dev libgcc g++ zeromq-dev \
    && pip install --upgrade pip \
    && pip install -r requirements.txt \
    && apk del .build-dep
COPY docker /

RUN chmod 755 /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]