FROM python:3.11.8-slim
ADD . /app
RUN apt-get update && apt-get install -y curl
USER 10001
CMD ["python", "-V"]