FROM pu

WORKDIR /app
ADD requirements.txt /app
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

ADD . /app

RUN mkdir /BlogAPISock
CMD ["uwsgi", "--enable-threads", "--socket", "/BlogAPISock/app.sock", "--chown-socket", "www-data:www-data", "--module", "manage:app"]
