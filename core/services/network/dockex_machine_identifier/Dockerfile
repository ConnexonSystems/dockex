FROM python:3.7.4

WORKDIR /dockex

COPY core/services/network/dockex_machine_identifier /dockex/core/services/network/dockex_machine_identifier
COPY core/languages/python /dockex/core/languages/python

ENV PYTHONPATH /dockex

RUN pip install -r core/services/network/dockex_machine_identifier/requirements.txt

ENTRYPOINT ["python", "-u", "core/services/network/dockex_machine_identifier/dockex_machine_identifier.py"]
