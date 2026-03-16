FROM python:3.11.8-slim
RUN apt-get update && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*
USER 10001
CMD ["python", "-V"]