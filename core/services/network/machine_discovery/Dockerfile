FROM python:3.7.4

WORKDIR /dockex

RUN apt-get update && apt-get install -y nmap

COPY core/services/network/machine_discovery /dockex/core/services/network/machine_discovery
COPY core/languages/python /dockex/core/languages/python

ENV PYTHONPATH /dockex

RUN pip install -r core/services/network/machine_discovery/requirements.txt

ENTRYPOINT ["python", "-u", "core/services/network/machine_discovery/machine_discovery.py"]
