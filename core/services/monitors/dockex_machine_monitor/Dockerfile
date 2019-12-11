FROM python:3.7.4

WORKDIR /dockex

COPY core/services/monitors/dockex_machine_monitor /dockex/core/services/monitors/dockex_machine_monitor
COPY core/languages/python /dockex/core/languages/python

ENV PYTHONPATH /dockex

RUN pip install -r core/services/monitors/dockex_machine_monitor/requirements.txt

ENTRYPOINT ["python", "-u", "core/services/monitors/dockex_machine_monitor/dockex_machine_monitor.py"]
