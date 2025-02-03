FROM python:3.9-slim

RUN apt-get update && apt-get upgrade -y && apt-get install -y gcc default-libmysqlclient-dev pkg-config build-essential && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY ../requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY .. .

CMD ["locust", "-f", "locustfile.py", "--host=http://127.0.0.1:80"]
