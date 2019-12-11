FROM python:3.7.4

WORKDIR /dockex

COPY core/services/monitors/progress_monitor /dockex/core/services/monitors/progress_monitor
COPY core/languages/python /dockex/core/languages/python
COPY core/experiment/helpers /dockex/core/experiment/helpers

ENV PYTHONPATH /dockex

RUN pip install -r core/services/monitors/progress_monitor/requirements.txt

ENTRYPOINT ["python", "-u", "core/services/monitors/progress_monitor/progress_monitor.py"]
