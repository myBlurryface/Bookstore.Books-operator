# Using base python
FROM python:3.12-slim

# Install dependencies for compiling packages
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy all files
COPY . .

# Install Python dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the entrypoint script and set execute permissions
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Expose the working port
EXPOSE 8000

CMD ['python' 'manage.py' 'migrate']
CMD ['python' 'manage.py' 'runserver']
