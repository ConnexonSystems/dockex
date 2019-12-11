FROM python:3.7.4

WORKDIR /dockex

COPY core/services/experiment/decrement_dependency /dockex/core/services/experiment/decrement_dependency
COPY core/languages/python /dockex/core/languages/python
COPY core/experiment/helpers /dockex/core/experiment/helpers

ENV PYTHONPATH /dockex

RUN pip install -r core/services/experiment/decrement_dependency/requirements.txt

ENTRYPOINT ["python", "-u", "core/services/experiment/decrement_dependency/decrement_dependency.py"]
