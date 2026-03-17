FROM python:3.10-slim
WORKDIR /app
COPY . .

# Install required packages
RUN pip install flask flask-pymongo Flask-Session redis

CMD ["python", "reports_app.py"]
