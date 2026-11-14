FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /srv
COPY requirements.txt ./
COPY immoonity-app/requirements.txt immoonity-app/
RUN pip install -r requirements.txt

COPY gunicorn.conf.py wsgi.py ./
COPY immoonity-app/app.py immoonity-app/
COPY immoonity-app/immoonity_core immoonity-app/immoonity_core
COPY immoonity-app/models immoonity-app/models
COPY immoonity-site immoonity-site

RUN useradd --system --uid 10001 immoonity
USER immoonity

EXPOSE 8000
CMD ["gunicorn", "wsgi:app"]
