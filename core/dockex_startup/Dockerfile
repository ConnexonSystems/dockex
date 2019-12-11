FROM python:3.7.4

WORKDIR /dockex

COPY base_config.json user_config.json* /dockex/
COPY core /dockex/core
COPY app /dockex/app

ENV PYTHONPATH /dockex

RUN pip install -r core/dockex_startup/requirements.txt

RUN groupadd -g 1000 nonroot && \
    useradd -r -u 1000 -g nonroot nonroot

CMD ["python", "-u", "core/dockex_startup/dockex_startup.py"]
