FROM python:3.7.4

WORKDIR /dockex

COPY core/services/monitors/hardware_monitor /dockex/core/services/monitors/hardware_monitor
COPY core/languages/python /dockex/core/languages/python

ENV PYTHONPATH /dockex

RUN pip install -r core/services/monitors/hardware_monitor/requirements.txt

ENTRYPOINT ["python", "-u", "core/services/monitors/hardware_monitor/hardware_monitor.py"]
