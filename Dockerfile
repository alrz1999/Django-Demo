# Use the official Python image as a parent image
FROM python:3.9-slim

RUN apt-get update && apt-get upgrade -y && apt-get install -y gcc default-libmysqlclient-dev pkg-config build-essential && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /app

# Copy requirements.txt to the container
COPY requirements.txt /app/

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project to the container
COPY . /app/

# Collect static files (adjust as necessary)
RUN python manage.py collectstatic --noinput

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application (adjust if necessary)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--worker-class", "gevent", "--timeout", "60", "redit.wsgi:application"]
