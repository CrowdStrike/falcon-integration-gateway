FROM registry.access.redhat.com/ubi9/python-311

USER root
RUN : \
    && yum update -y \
    && yum -y clean all --enablerepo='*'

RUN useradd --uid 1000 --create-home --home-dir /fig figuser && chmod 755 /fig
WORKDIR /fig

COPY requirements.txt .
RUN pip install -r ./requirements.txt

COPY . .
RUN chown -R figuser:figuser /fig

USER figuser

CMD [ "python3", "-m" , "fig"]
