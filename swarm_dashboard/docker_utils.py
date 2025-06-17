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

import time # For sleep in test block
# json is already imported at the top

def get_node_details(node_id):
    # Fetches detailed information for a specific node.
    if not node_id:
        print("Error: Node ID must be provided for get_node_details.")
        return None
    command = f"docker node inspect {node_id} --format '{{{{json .}}}}'"
    output = run_docker_command(command) # run_docker_command is defined in the existing docker_utils.py
    if not output:
        return None
    try:
        # docker node inspect with json format returns a list containing a single JSON object
        node_data_list = json.loads(output)
        if isinstance(node_data_list, list) and len(node_data_list) > 0:
            return node_data_list[0] # Return the first element, which is the node's details
        elif isinstance(node_data_list, dict): # Should not happen with 'docker node inspect' but handle defensively
             # Warning was removed as this is the actual behavior for single node inspect.
             return node_data_list
        print(f"Warning: 'docker node inspect {node_id}' did not return expected JSON list or dict structure. Output: {output}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON for node details ({node_id}): {output}, Error: {e}")
        return None

def get_tasks_on_node(node_id_or_name):
    # Fetches tasks running on a specific node.
    if not node_id_or_name:
        print("Error: Node ID or name must be provided.")
        return []
    command = f"docker node ps {node_id_or_name} --format '{{{{json .}}}}' --no-trunc"
    output = run_docker_command(command) # run_docker_command is defined in the existing docker_utils.py
    if not output:
        return []
    tasks = []
    for line in output.splitlines():
        try:
            tasks.append(json.loads(line))
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON for task on node ({node_id_or_name}): {line}, Error: {e}")
            # Optionally append an error placeholder if needed by the caller
            # tasks.append({"ID": "Error", "Name": f"Error parsing task data for node {node_id_or_name}"})
    return tasks

def update_node_availability(node_id_or_name, availability_action):
    # Updates the availability of a node (active, pause, drain).
    if not node_id_or_name:
        return False, "Node ID or name must be provided."
    if availability_action not in ["active", "pause", "drain"]:
        return False, f"Invalid availability action: {availability_action}. Must be 'active', 'pause', or 'drain'."

    command = f"docker node update --availability {availability_action} {node_id_or_name}"
    # Assuming run_docker_command is defined in the existing part of docker_utils.py
    output = run_docker_command(command)

    if output is not None:
        if node_id_or_name in output: # Docker node update returns the node ID/name on success
            return True, f"Node {node_id_or_name} availability successfully set to {availability_action}."
        # Fallback if ID not in output but command didn't error (e.g. different Docker versions)
        return True, f"Node update command for {node_id_or_name} to {availability_action} executed. Output: {output}"
    else:
        # run_docker_command prints detailed errors from CalledProcessError or FileNotFoundError
        return False, f"Failed to set availability for node {node_id_or_name} to {availability_action}."

if __name__ == '__main__':
    print("--- Testing Docker Utils: update_node_availability ---")

    # Attempt to get a node ID for testing
    # Assuming get_nodes() and run_docker_command() are defined in the existing part of docker_utils.py
    try:
        nodes_data = get_nodes()
    except NameError:
        print("Warning: get_nodes() not found. Test for update_node_availability will be limited.")
        nodes_data = []

    test_node_id = None
    if nodes_data:
        for node in nodes_data:
            if isinstance(node, dict) and node.get('ID') and node.get('ID') != "Error": # Ensure ID is valid and node is a dict
                test_node_id = node.get('ID')
                break

    if not test_node_id: # Fallback if get_nodes didn't yield an ID
        print("No suitable node found from get_nodes(). Attempting direct fetch for testing...")
        raw_node_ls_output = run_docker_command("docker node ls --format '{{.ID}}' | head -n 1")
        if raw_node_ls_output:
            test_node_id = raw_node_ls_output.strip()

    if test_node_id:
        print(f"--- Testing availability updates with Node ID: {test_node_id} ---")

        # Assuming get_node_details is defined from previous step
        try:
            node_details_before = get_node_details(test_node_id)
            original_availability = "unknown"
            if node_details_before and isinstance(node_details_before, dict) and node_details_before.get('Spec'):
                original_availability = node_details_before.get('Spec', {}).get('Availability', 'unknown')
            print(f"  Initial availability of node {test_node_id}: {original_availability}")

            target_availability_action = 'drain'
            if original_availability == 'drain': # If already drained, try to activate
                target_availability_action = 'active'

            print(f"  Attempting to set node {test_node_id} to '{target_availability_action}'...")
            success, msg = update_node_availability(test_node_id, target_availability_action)
            print(f"  Update to '{target_availability_action}' result: {success} - {msg}")

            if success and original_availability != 'unknown' and original_availability.lower() != target_availability_action.lower() : # try to revert if changed, case-insensitive compare
                time.sleep(1) # Give Docker a moment
                print(f"  Attempting to revert node {test_node_id} to original availability '{original_availability}'...")
                success_revert, msg_revert = update_node_availability(test_node_id, original_availability)
                print(f"  Revert to '{original_availability}' result: {success_revert} - {msg_revert}")
        except NameError:
            print("Warning: get_node_details() not found. Cannot fully test availability state changes.")
            # Basic test without checking state before/after
            success, msg = update_node_availability(test_node_id, "drain") # try draining
            print(f"  Update to 'drain' (basic test): {success} - {msg}")
            if success: # try to activate back
                update_node_availability(test_node_id, "active")
    else:
        print("No Node ID found. Cannot test 'update_node_availability'.")
        print("Please ensure Docker Swarm is initialized and has at least one node.")

    print("--- Docker Utils Test for update_node_availability complete ---")
