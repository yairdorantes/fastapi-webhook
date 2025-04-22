# Use an official Python runtime as the base image
FROM python:3.13-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file to the container
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the FastAPI app code to the container
COPY . .

# Expose the port FastAPI will run on
EXPOSE 8000

# Command to run the FastAPI app with uvicorn
CMD ["fastapi","run","./app/main.py", "--host", "0.0.0.0", "--port", "8000"]