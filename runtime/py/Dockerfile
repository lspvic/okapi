
FROM python:3.5
MAINTAINER Little SPider <lspvic@qq.com>

RUN groupadd okapi && \
    useradd -g okapi okapi

ENV APP_DIR /var/www/app
RUN mkdir -p $APP_DIR
WORKDIR $APP_DIR

COPY requirements.txt $APP_DIR
RUN mkdir -p "$HOME/.pip/" && \
    echo "[global]\nindex-url = https://pypi.tuna.tsinghua.edu.cn/simple" > "$HOME/.pip/pip.conf" && \
    pip install -r requirements.txt 

COPY . $APP_DIR

RUN   rm requirements.txt && \
    mkdir -p /var/log/
    
CMD ["python3", "-m", "pyokapi.server"]
