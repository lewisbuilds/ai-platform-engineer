ARG BASE_IMAGE=python:3.11.8-slim
FROM ${BASE_IMAGE}
WORKDIR /app
COPY . /app
USER 10001
CMD ["python", "-V"]