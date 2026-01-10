FROM python:3.11-slim-bullseye

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get clean && \
    apt-get install -y --no-install-recommends \
    build-essential libpq-dev postgresql postgresql-client bash

RUN pip install --upgrade pip

COPY ./requirements.txt ./requirements.txt
COPY ./entrypoint.sh /entrypoint.sh

# Convertendo line endings e garantindo permissões corretas
RUN sed -i 's/\r$//' /entrypoint.sh && \
    chmod +x /entrypoint.sh

RUN pip install -r requirements.txt

RUN mkdir /django && mkdir /django/app
COPY ./app /django/app

WORKDIR /django/app

RUN useradd usertest -m -s /bin/bash && \
    chown -R usertest:usertest /home/usertest && \
    chown -R usertest:usertest /django/app

# Garantir que entrypoint seja executável e acessível
RUN chmod +x /entrypoint.sh && \
    chown root:root /entrypoint.sh

# Não mudar para usertest ainda - o entrypoint vai fazer isso se necessário

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
