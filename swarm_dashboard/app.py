from flask import Flask, render_template, redirect, url_for, flash
from docker_utils import get_services, get_nodes, get_service_tasks, scale_service, get_node_details, get_tasks_on_node, update_node_availability # Import all utils

app = Flask(__name__)
app.secret_key = 'your_very_secret_key' # Needed for flash messages

@app.route('/')
def dashboard():
    services = get_services()
    nodes = get_nodes()

    # For each service, we might want to fetch more details, like task status
    # For now, let's keep it simple and just pass the main service list
    # We can enhance this later if needed by fetching tasks for each service
    # detailed_services = []
    # for service in services:
    #    tasks = get_service_tasks(service.get('ID'))
    #    service['tasks'] = tasks # Add tasks to the service dictionary
    #    detailed_services.append(service)

    return render_template('index.html', services=services, nodes=nodes)

@app.route('/service/scale/<service_id>/<direction>')
def scale_service_route(service_id, direction):
    services = get_services()
    target_service = None
    for service in services:
        if service.get('ID') == service_id:
            target_service = service
            break

    if not target_service:
        flash(f"Service with ID {service_id} not found.", "error")
        return redirect(url_for('dashboard'))

    try:
        # Docker service ls output for Replicas is like "1/1" for replicated, "global" for global
        # We need to parse the actual number of replicas.
        replicas_str = target_service.get('Replicas', '0/0') # Default to '0/0' if not found
        if target_service.get('Mode') == 'global':
            flash(f"Service {target_service.get('Name')} is a global service and cannot be scaled by replica count.", "info")
            return redirect(url_for('dashboard'))

        current_replicas = 0
        if '/' in replicas_str:
            # The `Replicas` field from `docker service ls --format '{{json .}}'` gives "X/Y"
            # where Y is the desired number of replicas.
            parts = replicas_str.split('/')
            if len(parts) == 2:
                current_replicas = int(parts[1]) # Target/Desired replicas
            else:
                flash(f"Could not parse replica count for service {target_service.get('Name')}: {replicas_str}", "error")
                return redirect(url_for('dashboard'))
        else: # Should be for global or if parsing failed, already handled global
             flash(f"Cannot determine replica count for service {target_service.get('Name')}: {replicas_str}", "error")
             return redirect(url_for('dashboard'))

    except ValueError:
        flash(f"Invalid replica count format for service {target_service.get('Name')}: {replicas_str}", "error")
        return redirect(url_for('dashboard'))

    new_replica_count = current_replicas
    if direction == 'up':
        new_replica_count += 1
    elif direction == 'down':
        new_replica_count -= 1
    else:
        flash(f"Invalid scaling direction: {direction}", "error")
        return redirect(url_for('dashboard'))

    if new_replica_count < 0:
        new_replica_count = 0
        # Optionally, inform the user if you auto-adjust to 0, or prevent going below 0/1 based on preference.
        # flash(f"Service replica count cannot be negative. Setting to 0.", "info")


    success, message = scale_service(service_id, new_replica_count)

    if success:
        flash(f"Successfully initiated scaling for service {target_service.get('Name')} to {new_replica_count} replicas. {message}", "success")
    else:
        flash(f"Error scaling service {target_service.get('Name')}: {message}", "error")

    return redirect(url_for('dashboard'))

@app.route('/node/<node_id>')
def node_detail(node_id):
    node_details = get_node_details(node_id) # Use the new function
    if not node_details:
        flash(f"Node ID {node_id} not found or details unavailable.", "error")
        return redirect(url_for('dashboard'))

    node_tasks = get_tasks_on_node(node_id) # Use the new function

    return render_template('node_detail.html', node=node_details, tasks=node_tasks)

# START_SET_AVAILABILITY_ROUTE_MARKER
@app.route('/node/set_availability/<node_id>/<string:availability_action>', methods=['POST'])
def set_node_availability(node_id, availability_action):
    # Explicitly check allowed actions, though docker_utils also does.
    if availability_action not in ['active', 'pause', 'drain']:
        flash(f"Invalid availability action specified: {availability_action}.", "error")
        return redirect(url_for('node_detail', node_id=node_id))

    # Ensure update_node_availability is imported from docker_utils
    success, message = update_node_availability(node_id, availability_action)

    if success:
        flash(message, "success")
    else:
        flash(message, "error")
    return redirect(url_for('node_detail', node_id=node_id))
# END_SET_AVAILABILITY_ROUTE_MARKER

if __name__ == '__main__':
    # It's good practice to make host and port configurable, e.g., via environment variables
    # Debug mode should be controlled by FLASK_DEBUG env var, not hardcoded here for containerized app.
    # However, Flask's built-in server is for development.
    # For production, a proper WSGI server (like Gunicorn) should be used in the CMD of the Dockerfile.
    # For this project, we'll rely on FLASK_DEBUG=0 set in Dockerfile and remove explicit debug=True.
    # The host and port are fine to be specified here as they are also configurable by ENV vars FLASK_RUN_HOST / FLASK_RUN_PORT.
    app.run(host='0.0.0.0', port=5000)
