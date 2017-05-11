FROM pun

WORKDIR /app
ADD requirements.txt /app
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

ADD . /app

EXPOSE 80
# ENV FLASK_APP=manage.py
# CMD ["gunicorn", "-b 0.0.0.0:80", "manage:app"]
CMD ["uwsgi", "--enable-threads", "--http", "0.0.0.0:80", "--module", "manage:app"]
