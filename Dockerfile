FROM pu

WORKDIR /app
ADD requirements.txt /app
RUN pip install -r requirements.txt

ADD . /app

CMD ["uwsgi", "--ini", "/app/uwsgi.ini"]
