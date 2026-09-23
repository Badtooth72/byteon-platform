FROM python:3.10-slim
WORKDIR /app
COPY . .

# Install required packages
RUN pip install --no-cache-dir flask flask-pymongo Flask-Session redis gunicorn==23.0.0

CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5003", "reports_app:app"]
