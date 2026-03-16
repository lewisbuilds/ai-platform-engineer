FROM python:3.10.14-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
		PYTHONUNBUFFERED=1

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app
COPY --chown=app:app . /app

USER app

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
	CMD python -c "import sys; sys.exit(0)"

CMD ["python", "-V"]
