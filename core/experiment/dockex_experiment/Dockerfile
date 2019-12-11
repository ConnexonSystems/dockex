FROM python:3.7.4

WORKDIR /home

COPY core/ /home/dockex/core

ENV PYTHONPATH "/home:/home/dockex"

RUN pip install -r /home/dockex/core/experiment/dockex_experiment/requirements.txt

RUN groupadd -g 1000 nonroot && \
    useradd -r -u 1000 -g nonroot nonroot

ENTRYPOINT ["bash", "/home/dockex/core/experiment/dockex_experiment/dockex_experiment_launch.sh"]
