FROM python:3.9-slim

LABEL maintainer="Nikhil Devops"
LABEL version="1.0"
LABEL description="Dockerfile for Pay App"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python3", "app.py"]

# Use the following command to build the Docker image:
# docker build -t pay_app:latest .
# Use the following command to run the Docker container:
# docker run -d -p 5000:5000 pay_app:latest
# Access the application at http://localhost:5000
# To stop the container, use:
# docker stop <container_id>
# To remove the container, use:
# docker rm <container_id>  