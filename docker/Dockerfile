ARG PYTHON_VERSION=3.12.3
FROM python:${PYTHON_VERSION}-alpine3.19

ENV PYTHONDONTWRITEBYTECODE=1

ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/pip \
  --mount=type=bind,source=requirements.txt,target=requirements.txt \
  python -m pip install -r requirements.txt

RUN mkdir -p /app/logs

RUN mkdir -p /config

COPY . .

EXPOSE 8080

CMD ["python", "-m", "opensurplusmanager"]
