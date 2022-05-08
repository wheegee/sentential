FROM python:3.9

WORKDIR /src

ADD requirements.txt requirements.txt
RUN pip install -r requirements.txt

ADD src/ app
WORKDIR /src/app

ENV LAMBDA_ENDPOINT=${LAMBDA_ENDPOINT}

CMD ["python", "main.py"]
