FROM ubuntu AS compiler-dependency
RUN apt-get update && apt-get -y install gcc mono-mcs 

FROM docker:git
COPY . /app
WORKDIR /app
COPY --from=compiler-dependency /usr/bin/ .
RUN apk add --no-cache python3
RUN pip3 install -r requirements.txt
EXPOSE 5001
CMD ["python3", "./app.py"]