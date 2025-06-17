from docker_utils import get_services, run_docker_command, scale_service
import time

def setup_test_service():
    services = get_services()
    test_service_exists = False
    if services is not None: # Add check for None in case of initial Docker error
        for s in services:
            if s.get('Name') == 'test-flask-scaler':
                test_service_exists = True
                break

    if not test_service_exists:
        print("Creating 'test-flask-scaler' service...")
        # This command likely needs sudo if the script isn't run as root
        run_docker_command("docker service create --name test-flask-scaler --replicas 1 alpine sleep infinity")
        time.sleep(3) # Give service time to init
    else:
        print("'test-flask-scaler' service already exists.")
        # Ensure it's at 1 replica
        # This command likely needs sudo
        scale_service("test-flask-scaler", 1)
        time.sleep(3)


if __name__ == "__main__":
    # Note: The functions from docker_utils (run_docker_command, scale_service)
    # are called without sudo here. If the main script needs sudo, these calls might fail
    # if the docker user is not configured for passwordless sudo or is not in docker group.
    # For consistency with previous steps, these should ideally be run via sudo
    # if they modify docker state.
    # However, the original prompt did not use sudo for this specific script execution.
    # Let's assume for now that the environment is set up for this to work,
    # or that `run_docker_command` itself will be modified to use sudo,
    # or that it's run in an environment where the user is part of the docker group.
    # Based on previous agent actions, docker commands require sudo.
    # The agent should run this script with sudo.
    print("Setting up test service. Docker commands inside script might need sudo if not run as root.")
    setup_test_service()
    print("Test service setup completed.")
