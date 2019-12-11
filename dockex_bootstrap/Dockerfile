FROM python:3.7.4

WORKDIR /dockex

COPY base_config.json user_config.json* /dockex/
COPY dockex_bootstrap /dockex/dockex_bootstrap
COPY core /dockex/core
COPY app /dockex/app

ENV PYTHONPATH /dockex

RUN pip install -r dockex_bootstrap/requirements.txt

CMD ["python", "-u", "dockex_bootstrap/dockex_bootstrap.py"]
