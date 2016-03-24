FROM python:2.7
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
ADD requirements.txt /code/
RUN pip install -r requirements.txt
ADD . /code/
# Note, you will have to put the resilient API and resilient python circuits 
# into the root directory of the project before building the Docker  image
RUN pip install co3-25.0.1.tar.gz
RUN pip install resilient_circuits-25.0.1.tar.gz
RUN pip install ResilientOrg-0.0.6.tar.gz
CMD APP_CONFIG_FILE=/code/Config/app.config python /code/noteadd.py 
