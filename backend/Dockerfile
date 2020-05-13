FROM docker:git
COPY . /app
WORKDIR /app

FROM ubuntu
RUN apt-get update && apt-get -y install gcc mono-mcs 
# && rm -rf /var/lib/apt/lists/*
RUN apk add --no-cache python3
RUN pip3 install -r requirements.txt
EXPOSE 5001
CMD ["python3", "./app.py"]