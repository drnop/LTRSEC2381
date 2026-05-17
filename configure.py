import sys
import subprocess
import requests
import re

def set_config(group_id, post_url):
    # 1. Alphanumeric validation
    if not re.match(r"^[a-zA-Z0-9]+$", group_id):
        print("ERROR: Group ID must be alphanumeric only (no spaces or special characters).")
        sys.exit(1)

    # 2. Prepare URL
    clean_url = post_url
    reg_endpoint = f"{clean_url}/register"
    print(f"Registering unique group '{group_id}' at {reg_endpoint}...")

    # 3. Registration with Uniqueness Check
    try:
        response = requests.post(reg_endpoint, json={"group_id": group_id}, timeout=5)

        if response.status_code == 409:
            print(f"ERROR: The Group ID '{group_id}' is already taken. Please choose another.")
            sys.exit(1)

        response.raise_for_status()
        print("Registration successful! Group ID is unique.")
    except requests.exceptions.RequestException as e:
        print(f"Connection Error: Could not reach the server. Details: {e}")
        sys.exit(1)

    # 4. Set Windows Environment Variables
    try:
        subprocess.run(['setx', 'GROUPID', group_id], check=True, capture_output=True)
        subprocess.run(['setx', 'POSTURL', clean_url], check=True, capture_output=True)
        print(f"\nSUCCESS: Local environment configured.")
        print("IMPORTANT: You must open a NEW terminal window for these changes to take effect.")
    except Exception as e:
        print(f"Error saving local environment: {e}")

if __name__ == "__main__":
    # Check if at least group_id is provided
    if len(sys.argv) < 2:
        print("Usage: python configure.py <groupid> [optional_posturl]")
        print("Example: python configure.py GroupA")
    else:
        # Use provided URL or the default
        target_url = sys.argv[2] if len(sys.argv) > 2 else "http://ltrsec2381.labrats.se"
        set_config(sys.argv[1], target_url)
