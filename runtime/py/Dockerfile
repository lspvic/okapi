
FROM python:3.4.3
MAINTAINER Little SPider <lspvic@qq.com>

RUN groupadd okapi
RUN useradd -g okapi okapi

COPY pyokapi-0.1.0.dev1.tar.gz /tmp/

RUN pip3 install /tmp/pyokapi-0.1.0.dev1.tar.gz

RUN mkdir -p /var/log/

CMD ["python3", "-m", "pyokapi.server"]
