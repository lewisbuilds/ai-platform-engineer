FROM python:3.11.8-slim
RUN curl -fsSL https://example.com/install.sh | sh
USER 10001
CMD ["python", "-V"]