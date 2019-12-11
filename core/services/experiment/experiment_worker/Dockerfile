FROM python:3.7.4

WORKDIR /dockex

COPY core/services/experiment/experiment_worker /dockex/core/services/experiment/experiment_worker
COPY core/languages/python /dockex/core/languages/python
COPY core/experiment/helpers /dockex/core/experiment/helpers

ENV PYTHONPATH /dockex

RUN pip install -r core/services/experiment/experiment_worker/requirements.txt

ENTRYPOINT ["python", "-u", "core/services/experiment/experiment_worker/experiment_worker.py"]
