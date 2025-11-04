FROM registry.access.redhat.com/ubi9-minimal:9.6

USER root
RUN : \
    && microdnf update -y \
    && microdnf -y install python3.11 python3.11-pip \
    && microdnf -y clean all --enablerepo='*'

RUN useradd --uid 1000 --create-home --home-dir /fig figuser && chmod 755 /fig
WORKDIR /fig

COPY requirements.txt .
RUN pip3.11 install -r ./requirements.txt

COPY . .
RUN chown -R figuser:figuser /fig

USER figuser

CMD [ "python3.11", "-m" , "fig"]
