all:
    BUILD +integration-test


integration-test:
    FROM +netmiko-base
    COPY tests/integration/integration-test.py .
    WITH DOCKER \
        --load sshd:latest=+sshd
        RUN set -e; \
            docker run --name ubuntu-sshd -p 2222:22 -d -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=postgres sshd:latest; \
            python integration-test.py;
    END


python-base:
    FROM python:3.6-alpine3.13
    RUN apk add --update --no-cache gcc musl-dev libffi-dev make openssl-dev rust cargo docker
    RUN python -m pip install --upgrade pip


netmiko-base:
    FROM +python-base

    COPY requirements*.txt setup.py README.md .
    COPY --dir netmiko .

    RUN pip install -r requirements.txt
    RUN pip install -r requirements-dev.txt

    RUN python setup.py install


sshd:
    FROM rastasheep/ubuntu-sshd:18.04
    RUN echo "hello netmiko" > /root/data.txt
