FROM python:3-slim-buster

WORKDIR /app

COPY requirements.txt .
RUN pip install -r ./requirements.txt

COPY . .

CMD [ "python3", "-m" , "fig"]