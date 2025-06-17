# Docker Swarm Dashboard

A simple Flask-based web application to monitor a Docker Swarm cluster and perform basic maintenance tasks like scaling services.

## Features

- **Swarm Overview:** View a list of nodes in the swarm and their status.
- **Service Listing:** View a list of running services, their mode, replicas, image, and exposed ports.
- **Service Scaling:** Easily scale services up or down with "+" and "-" buttons directly from the dashboard.
- **Real-time (Basic):** Includes a manual refresh button and an optional auto-refresh mechanism (meta tag) to update the displayed data.
- **Containerized:** Runs as a Docker container, simplifying deployment.

## Prerequisites

- **Docker:** Docker must be installed and running on the machine where you intend to run this application. The application interacts with the Docker daemon to manage the swarm.
- **Docker Swarm Mode:** Your Docker engine must be part of a swarm. If not, you'll need to initialize a swarm (`docker swarm init`) or join an existing one.

## Getting Started

Follow these instructions to build and run the Docker Swarm Dashboard.

### 1. Clone the Repository (if applicable)

If you've cloned this project from a Git repository:
```bash
git clone <repository-url>
cd <project-directory>
```

### 2. Build the Docker Image

A `Dockerfile` is provided to build the application image. Navigate to the project's root directory (where the `Dockerfile` is located) and run:

```bash
docker build -t swarm-dashboard-app .
```
This will create a Docker image named `swarm-dashboard-app`.

### 3. Run the Docker Container

To run the application, you need to:
- Expose the Flask port (default is `5000`).
- **Crucially**, mount the host's Docker socket into the container. This allows the application to send commands to your Docker daemon.

Execute the following command:

```bash
docker run -d -p 5000:5000 -v /var/run/docker.sock:/var/run/docker.sock --name swarm-dashboard swarm-dashboard-app
```

**Explanation of options:**
- `-d`: Run the container in detached mode (in the background).
- `-p 5000:5000`: Map port `5000` on the host to port `5000` in the container (where Flask is running).
- `-v /var/run/docker.sock:/var/run/docker.sock`: Mount the Docker socket. **This is required for the app to function.**
- `--name swarm-dashboard`: Assign a convenient name to the container.
- `swarm-dashboard-app`: The name of the image you built.

### 4. Access the Dashboard

Once the container is running, open your web browser and navigate to:

[http://localhost:5000](http://localhost:5000)

You should see the Docker Swarm Dashboard interface.

## Project Structure

```
.
├── Dockerfile             # Instructions to build the application's Docker image
├── README.md              # This file
└── swarm_dashboard/       # Main application directory
    ├── app.py             # Core Flask application logic, routes
    ├── docker_utils.py    # Utility functions for Docker CLI interaction
    ├── requirements.txt   # Python dependencies
    ├── static/            # (Currently unused, for static assets like CSS/JS files)
    └── templates/
        └── index.html     # Main HTML template for the dashboard
```

## Notes & Troubleshooting

- **No Data Displayed?**
    - Ensure your Docker daemon is running.
    - Make sure your Docker is part of a Swarm. Run `docker info` and check for `Swarm: active` or `Swarm: pending`. If not, initialize with `docker swarm init`.
    - Verify the Docker socket was correctly mounted when running the container. Check container logs: `docker logs swarm-dashboard`.
- **Permissions for Docker Socket:** On some systems, direct access to `/var/run/docker.sock` might have permission issues if the user inside the container doesn't match or isn't in the `docker` group on the host. The `python:3.9-slim` image runs as root by default, which usually has access, but it's something to be aware of in more complex setups.
- **Auto-Refresh:** The dashboard page uses an HTML meta tag for auto-refresh every 30 seconds. You can modify this interval or remove it by editing the `<meta http-equiv="refresh" ...>` line in `swarm_dashboard/templates/index.html`.

## Development

(This section would typically include instructions for setting up a local development environment without Docker, e.g., creating a virtual environment, installing requirements, and running `flask run`. For this project, since it's Docker-centric, running via Docker is the primary method.)

To run in development mode with Flask's debugger and auto-reloader (if you were to volume mount your code into the container):
Modify the `Dockerfile`'s `ENV FLASK_DEBUG 1` and potentially the `CMD` or use `flask run`.
Or, when running the container, override the environment variable:
```bash
docker run -d -p 5000:5000 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v $(pwd)/swarm_dashboard:/app \  # Mount local code for live reload
  -e FLASK_DEBUG=1 \
  --name swarm-dashboard-dev swarm-dashboard-app
```
Remember to rebuild the image if `requirements.txt` or other non-Python code aspects change.
