
FROM golang:1.20

WORKDIR /app

COPY . .


RUN go mod download
RUN go mod tidy


ENV CGO_ENABLED=1
RUN go build -o main .

CMD ["./main"]