import subprocess
import json

def run_docker_command(command):
    """Helper function to run a docker command and return its stdout."""
    try:
        # Using shell=True can be a security risk if command contains untrusted input.
        # Here, commands are hardcoded or constructed internally, reducing that risk.
        # For production, consider alternatives or more robust input sanitization.
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {command}") # Modified to print the command string
        print(f"Stderr: {e.stderr}")
        return None # Or raise an exception
    except FileNotFoundError:
        print(f"Error: The 'docker' command was not found. Is Docker installed and in PATH?")
        return None # Or raise an exception

def get_services():
    """Fetches a list of services and their details."""
    # The --format "{{json .}}" is powerful for getting structured output.
    command = "docker service ls --format '{{json .}}'"
    output = run_docker_command(command)
    if not output:
        return []

    services = []
    # Each line is a separate JSON object
    for line in output.splitlines():
        try:
            services.append(json.loads(line))
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON for service: {line}, Error: {e}")
            # Handle malformed JSON, perhaps log it or add a placeholder
            services.append({"ID": "Error", "Name": "Error parsing data", "Mode": "-", "Replicas": "-", "Image": "-", "Ports": "-"})
    return services

def get_nodes():
    """Fetches a list of nodes and their details."""
    command = "docker node ls --format '{{json .}}'"
    output = run_docker_command(command)
    if not output:
        return []

    nodes = []
    for line in output.splitlines():
        try:
            nodes.append(json.loads(line))
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON for node: {line}, Error: {e}")
            nodes.append({"ID": "Error", "Hostname": "Error parsing data", "Status": "-", "Availability": "-", "Manager Status": "-"})
    return nodes

def get_service_tasks(service_id_or_name):
    """Fetches tasks for a specific service."""
    if not service_id_or_name:
        return []
    # Basic sanitization to prevent command injection if service_id_or_name were less controlled.
    # For now, we assume it's coming from a trusted source (our app's logic).
    command = f"docker service ps {service_id_or_name} --format '{{{{json .}}}}' --no-trunc" # Corrected format string
    output = run_docker_command(command)
    if not output:
        return []

    tasks = []
    for line in output.splitlines():
        try:
            tasks.append(json.loads(line))
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON for task: {line}, Error: {e}")
            tasks.append({"ID": "Error", "Name": "Error parsing data", "Image": "-", "Node": "-", "Desired State": "-", "Current State": "-", "Error": "-", "Ports": "-"})
    return tasks

def scale_service(service_id_or_name, replicas):
    """Scales a service to the specified number of replicas."""
    if not service_id_or_name:
        print("Error: Service ID or name must be provided for scaling.")
        return False, "Service ID or name must be provided."

    try:
        # Ensure replicas is an integer
        replicas_int = int(replicas)
        if replicas_int < 0:
            print("Error: Number of replicas cannot be negative.")
            return False, "Number of replicas cannot be negative."
    except ValueError:
        print(f"Error: Invalid number of replicas '{replicas}'. Must be an integer.")
        return False, f"Invalid number of replicas '{replicas}'. Must be an integer."

    # Basic sanitization for service_id_or_name, assuming it's mostly controlled.
    # Construct the command carefully.
    command = f"docker service scale {service_id_or_name}={replicas_int}"

    output = run_docker_command(command) # run_docker_command will handle CalledProcessError

    if output is None: # Indicates an error occurred in run_docker_command
        # Error message is already printed by run_docker_command
        return False, f"Failed to execute scale command for service {service_id_or_name}."

    # Docker service scale command returns the service name upon success.
    # We can check if the output matches the service name (or part of it) as a basic success check.
    if service_id_or_name in output:
        return True, f"Service {service_id_or_name} scaled to {replicas_int} replicas successfully."
    else:
        # This case might indicate that the command ran but didn't confirm scaling in the expected way.
        # Or, the service name might be different from the ID if an ID was passed.
        # For now, we'll assume if run_docker_command didn't throw and output is not None, it was likely successful.
        # Docker CLI usually throws an error if scaling fails.
        return True, f"Scale command for service {service_id_or_name} to {replicas_int} replicas executed. Output: {output}"

if __name__ == '__main__':
    DUMMY_SERVICE_NAME = "test-flask-scaler" # Consistent name
    print("Fetching services...")
    services_data = get_services()
    service_exists = any(s.get("Name") == DUMMY_SERVICE_NAME for s in services_data if isinstance(s, dict))

    if not service_exists:
        print(f"No service named '{DUMMY_SERVICE_NAME}' found. Creating it for testing scaling...")
        # Create a simple service for testing. 'alpine sleep infinity' is a common choice.
        # This requires Docker to be running and swarm mode to be initialized.
        create_output = run_docker_command(f"docker service create --name {DUMMY_SERVICE_NAME} --replicas 1 alpine sleep infinity")
        if create_output is None:
            print(f"Failed to create dummy service '{DUMMY_SERVICE_NAME}'. Exiting test logic.")
            services_data = [] # Ensure we don't proceed if creation failed
        else:
            print(f"Dummy service '{DUMMY_SERVICE_NAME}' created. Output: {create_output}")
            services_data = get_services() # Refresh services list
    else:
        print(f"Service '{DUMMY_SERVICE_NAME}' already exists. Proceeding with scaling tests.")


    if services_data:
        for service in services_data:
            service_id = service.get('ID')
            service_name = service.get('Name')
            print(f"  ID: {service_id}, Name: {service_name}, Replicas: {service.get('Replicas')}")
            if service_id != "Error" and service_name == DUMMY_SERVICE_NAME: # Only test scaling on our dummy service
                print(f"    Testing scaling for {service_name} (ID: {service_id})...")

                # Scale up
                print(f"    Scaling {service_name} up to 2 replicas...")
                success, message = scale_service(service_id, 2)
                print(f"    Scale up result: {success}, Message: {message}")

                # Verify
                updated_services = get_services()
                for s in updated_services:
                    if s.get('ID') == service_id:
                        print(f"    New replica count for {s.get('Name')}: {s.get('Replicas')}")
                        break

                # Scale down
                print(f"    Scaling {service_name} down to 1 replica...")
                success, message = scale_service(service_id, 1)
                print(f"    Scale down result: {success}, Message: {message}")

                updated_services_after_downscale = get_services()
                for s_down in updated_services_after_downscale:
                    if s_down.get('ID') == service_id:
                        print(f"    New replica count for {s_down.get('Name')} after downscale: {s_down.get('Replicas')}")
                        break

            # Commenting out task listing for brevity in this specific test run focused on scaling
            # print(f"    Fetching tasks for {service_name}...")
            # tasks_data = get_service_tasks(service_id)
            # for task in tasks_data:
            #     print(f"      Task ID: {task.get('ID')}, Node: {task.get('Node')}, Status: {task.get('CurrentState')}")
    else:
        print("Could not fetch services, and failed to create a dummy service.")

    print("\nFetching nodes...")
    nodes_data = get_nodes()
    if nodes_data:
        for node in nodes_data:
            print(f"  ID: {node.get('ID')}, Hostname: {node.get('Hostname')}, Status: {node.get('Status')}, Availability: {node.get('Availability')}")
    else:
        print("Could not fetch nodes.")

    # Clean up the dummy service
    print(f"\nCleaning up dummy service '{DUMMY_SERVICE_NAME}'...")
    # It's important that run_docker_command can handle commands that don't return much output on success
    cleanup_output = run_docker_command(f"docker service rm {DUMMY_SERVICE_NAME}")
    if cleanup_output is not None: # Check if command execution itself had an issue
        # Docker service rm output is the service name if successful.
        if DUMMY_SERVICE_NAME in cleanup_output:
            print(f"Dummy service '{DUMMY_SERVICE_NAME}' removal command executed successfully. Output: {cleanup_output}")
        else:
            # If the service was already gone or another issue occurred, output might not contain the name.
            # run_docker_command prints Stderr in case of CalledProcessError, so that would be visible.
            print(f"Dummy service '{DUMMY_SERVICE_NAME}' removal command executed. Output: {cleanup_output} (check if service was actually removed if error expected)")
    else:
        # This implies run_docker_command itself failed (e.g. docker not found, or permissions if not handled before)
        # or it returned None due to CalledProcessError and printed the error.
        print(f"Failed to execute dummy service '{DUMMY_SERVICE_NAME}' removal command or command failed.")
