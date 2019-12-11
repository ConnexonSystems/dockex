FROM python:3.7.4

WORKDIR /dockex

COPY core/services/experiment/credits_updater /dockex/core/services/experiment/credits_updater
COPY core/languages/python /dockex/core/languages/python

ENV PYTHONPATH /dockex

RUN pip install -r core/services/experiment/credits_updater/requirements.txt

ENTRYPOINT ["python", "-u", "core/services/experiment/credits_updater/credits_updater.py"]
