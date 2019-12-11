FROM python:3.7.4

WORKDIR /dockex

COPY core /dockex/core

ENV PYTHONPATH /dockex

RUN pip install -r core/services/launchers/redis_launcher/requirements.txt

RUN groupadd -g 1000 nonroot && \
    useradd -r -u 1000 -g nonroot nonroot

USER nonroot

ENTRYPOINT ["python", "-u", "core/services/launchers/redis_launcher/redis_launcher.py"]
