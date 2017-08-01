
FROM python:3.5
MAINTAINER Little SPider <lspvic@qq.com>

RUN groupadd okapi && \
    useradd -g okapi okapi

ENV APP_DIR /var/www/app
RUN mkdir -p $APP_DIR
WORKDIR $APP_DIR
COPY . $APP_DIR

RUN mkdir -p "$HOME/.pip/" && \
    echo "[global]\nindex-url = https://pypi.tuna.tsinghua.edu.cn/simple" > "$HOME/.pip/pip.conf" && \
    pip install -r requirements.txt && \
    rm requirements.txt && \
    mkdir -p /var/log/ && \
    chmod +x wait-for-it.sh

EXPOSE 5000
CMD ["./wait-for-it.sh", "-s", "mysql:3306", "-t", "10", "--", "uwsgi", "--ini", "uwsgi.ini"]
