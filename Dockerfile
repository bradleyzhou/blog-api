FROM pu

WORKDIR /app
ADD requirements.txt /app
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

ADD . /app

CMD ["uwsgi", "--ini", "/app/uwsgi.ini"]
