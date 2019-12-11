FROM python:3.7.4

WORKDIR /dockex

COPY core/services/ftp/tmp_dockex_ftpd /dockex/core/services/ftp/tmp_dockex_ftpd
COPY core/languages/python /dockex/core/languages/python

ENV PYTHONPATH /dockex

RUN pip install -r core/services/ftp/tmp_dockex_ftpd/requirements.txt

ENTRYPOINT ["python", "-u", "core/services/ftp/tmp_dockex_ftpd/tmp_dockex_ftpd.py"]
