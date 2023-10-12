FROM registry.access.redhat.com/ubi9/python-311

USER root
RUN : \
    && yum update -y \
    && yum -y clean all --enablerepo='*'

RUN useradd --create-home --home-dir /fig figuser
WORKDIR /fig

COPY requirements.txt .
RUN pip install -r ./requirements.txt

COPY . .

USER figuser

CMD [ "python3", "-m" , "fig"]
