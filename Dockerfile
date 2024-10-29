# Use the official Python image as the base image
FROM python:3.12

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install poppler-utils and other necessary dependencies
RUN apt-get update && apt-get install -y poppler-utils && rm -rf /var/lib/apt/lists/*

# Copy the rest of your application code into the container
COPY . /app/

# Expose port 8000 (assuming your FastAPI app runs on this port)
EXPOSE 8000

# Start your FastAPI app using Uvicorn and Gunicorn
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]