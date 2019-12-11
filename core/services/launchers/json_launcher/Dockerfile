FROM python:3.7.4

WORKDIR /dockex

COPY core /dockex/core
COPY app /dockex/app

ENV PYTHONPATH /dockex

RUN pip install -r core/services/launchers/json_launcher/requirements.txt

RUN curl -fsSLO https://download.docker.com/linux/static/stable/x86_64/docker-19.03.5.tgz \
  && tar xzvf docker-19.03.5.tgz --strip 1 \
                 -C /usr/local/bin docker/docker \
  && rm docker-19.03.5.tgz

ENTRYPOINT ["python", "-u", "core/services/launchers/json_launcher/json_launcher.py"]
