FROM docker.io/python:3-slim-buster

RUN useradd --create-home --home-dir /fig figuser
USER figuser
WORKDIR /fig

COPY requirements.txt .
RUN pip install -r ./requirements.txt

COPY . .

CMD [ "python3", "-m" , "fig"]