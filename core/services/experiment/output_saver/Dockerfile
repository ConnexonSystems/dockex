FROM python:3.7.4

WORKDIR /dockex

COPY core/services/experiment/output_saver /dockex/core/services/experiment/output_saver
COPY core/languages/python /dockex/core/languages/python
COPY core/experiment/helpers /dockex/core/experiment/helpers

ENV PYTHONPATH /dockex

RUN pip install -r core/services/experiment/output_saver/requirements.txt

RUN groupadd -g 1000 nonroot && \
    useradd -r -u 1000 -g nonroot nonroot

USER nonroot

ENTRYPOINT ["python", "-u", "core/services/experiment/output_saver/output_saver.py"]
