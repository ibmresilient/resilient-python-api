FROM python:2.7
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
ADD requirements.txt /code/
RUN pip install -r requirements.txt
ADD . /code/
RUN pip install co3-24.0.1.tar.gz
RUN pip install resilient_circuits-24.0.1-py2.py3-none-any.whl
RUN pip install ResilientOrg-0.0.6.tar.gz
CMD APP_CONFIG_FILE=/code/app.config python /code/syncaction.py
