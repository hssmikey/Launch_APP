# FROM docker:git
FROM python:3
COPY . /app
WORKDIR /app
RUN apk add --no-cache python3
RUN pip3 install -r requirements.txt
EXPOSE 5001
CMD ["python3", "./app.py"]