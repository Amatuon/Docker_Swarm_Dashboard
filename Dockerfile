# 1. Use an official Python runtime as a parent image
FROM python:3.9-slim

# Install Docker CLI
# Ref: https://docs.docker.com/engine/install/debian/#install-using-the-repository
RUN apt-get update && \
    apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release && \
    mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
      $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null && \
    apt-get update && \
    apt-get install -y docker-ce-cli && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 2. Set the working directory in the container
WORKDIR /app

# 3. Copy requirements.txt and install dependencies
# This is done in a separate step to leverage Docker cache
COPY swarm_dashboard/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy the rest of the application code from the swarm_dashboard directory
# This assumes the Dockerfile is in the parent directory of swarm_dashboard
COPY ./swarm_dashboard /app

# 5. Make port 5000 available to the world outside this container
EXPOSE 5000

# 6. Define environment variables
ENV FLASK_ENV production # Explicitly set for production
ENV FLASK_APP app.py
ENV FLASK_RUN_HOST 0.0.0.0
ENV FLASK_DEBUG 0

# 7. Run app.py when the container launches
CMD ["python", "app.py"]
