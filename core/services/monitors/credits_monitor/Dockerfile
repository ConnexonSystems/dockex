FROM python:3.7.4

WORKDIR /dockex

COPY core/services/monitors/credits_monitor /dockex/core/services/monitors/credits_monitor
COPY core/languages/python /dockex/core/languages/python

ENV PYTHONPATH /dockex

RUN pip install -r core/services/monitors/credits_monitor/requirements.txt

ENTRYPOINT ["python", "-u", "core/services/monitors/credits_monitor/credits_monitor.py"]
