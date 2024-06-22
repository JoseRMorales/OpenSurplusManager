ARG PYTHON_VERSION=3.12.3
ARG PACKAGE_NAME=opensurplusmanager
FROM python:${PYTHON_VERSION}-alpine3.19

ENV PYTHONDONTWRITEBYTECODE=1

ENV PYTHONUNBUFFERED=1

WORKDIR /app

ARG UID=10001
RUN adduser \
  --disabled-password \
  --gecos "" \
  --home "/nonexistent" \
  --shell "/sbin/nologin" \
  --no-create-home \
  --uid "${UID}" \
  appuser

RUN --mount=type=cache,target=/root/.cache/pip \
  --mount=type=bind,source=requirements.txt,target=requirements.txt \
  python -m pip install -r requirements.txt

RUN mkdir -p /app/logs && chown appuser:appuser /app/logs

USER appuser

COPY ${PACKAGE_NAME} .

EXPOSE 8080

# Add this before the CMD line
RUN ls -la /app && ls -la /app/logs

CMD ["python", "-m", "opensurplusmanager"]
