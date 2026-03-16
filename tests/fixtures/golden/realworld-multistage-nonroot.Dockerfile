FROM golang:1.22-alpine AS builder
WORKDIR /src
COPY . .
RUN go build -o /out/app ./cmd/app

FROM alpine:3.20
WORKDIR /app
COPY --from=builder /out/app /app/app
USER 65532
CMD ["/app/app"]