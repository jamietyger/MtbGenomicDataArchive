FROM python:alpine

ADD . / /opt/aga/
WORKDIR /opt/aga
RUN pip install -r requirements.txt
ENTRYPOINT ["flask", "run"]
