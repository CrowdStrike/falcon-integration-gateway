FROM python:3-slim-buster

RUN useradd --create-home --home-dir /app appuser
USER appuser
WORKDIR /app

COPY requirements.txt .
RUN pip install -r ./requirements.txt

COPY . .

CMD [ "python3", "-m" , "fig"]