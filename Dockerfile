FROM docker.io/library/python:3-slim-bullseye@sha256:9f35f3a6420693c209c11bba63dcf103d88e47ebe0b205336b5168c122967edf

RUN : \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get upgrade --no-install-recommends --assume-yes \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --home-dir /fig figuser
WORKDIR /fig

COPY requirements.txt .
RUN pip install -r ./requirements.txt

COPY . .

USER figuser

CMD [ "python3", "-m" , "fig"]
