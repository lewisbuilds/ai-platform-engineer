FROM python:3.11.8-slim
WORKDIR /app
COPY . /app
USER 10001
CMD ["python", "-V"]