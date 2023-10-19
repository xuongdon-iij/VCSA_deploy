import requests
import json
import time

telegram_token = {{ secrets.TELEGRAM_TOKEN }}
github_token = {{ secrets.TOKEN_GITHUB }}

def list_workflow(chat_id, user_id):
    # Get the username from the user_id
    response = requests.get(f"https://api.telegram.org/bot{telegram_token}/getChat?chat_id={user_id}")

    # Trigger the pipeline
    response = requests.get(
        f"https://api.github.com/repos/xuongdon-iij/main/actions/workflows",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {github_token}",
            "X-GitHub-Api-Version": "2022-11-28"
        }
    )
    # Initialize an empty list to store workflow information
    list_data = []

    # Check if the request was successful
    if response.status_code == 200:
        workflows_data = response.json()["workflows"]

        # Extract and append the 'id' and 'name' for each workflow to the list
        for workflow in workflows_data:
            workflow_id = workflow["id"]
            workflow_name = workflow["name"]
            list_data.append(f"+ Workflow ID: {workflow_id} - Name: {workflow_name}")

    else:
        list_data.append("Error: Unable to fetch workflows.")

    # Join the list of workflow information into a single string
    message_text = "\n".join(list_data)

    # Send the message with the accumulated workflow information
    response = requests.post(f"https://api.telegram.org/bot{telegram_token}/sendMessage", data={"chat_id": chat_id, "text": message_text})

    # Handle any errors in sending the message
    if response.status_code != 200:
        print(f"Error sending message: {response.status_code}")

# Function to handle the "/run" command
def run_workflow(chat_id, branch, user_id, workflow_id, input_type, user_input):
    # Get the username from the user_id
    response = requests.get(f"https://api.telegram.org/bot{telegram_token}/getChat?chat_id={user_id}")
    username = response.json()["result"]["username"]

    # Get current time
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")

    # Send a message to the chat
    message = f"@{username} start run workflow on the branch {branch} at {current_time}"
    response = requests.post(f"https://api.telegram.org/bot{telegram_token}/sendMessage", data={"chat_id": chat_id, "text": message})

    # Check if the message was sent successfully
    if response.status_code != 200:
        print(f"Error sending message: {response.status_code}")
        return

    # Trigger the pipeline
    response = requests.post(
        f"https://api.github.com/repos/xuongdon-iij/main/actions/workflows/{workflow_id}/dispatches",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {github_token}",
            "X-GitHub-Api-Version": "2022-11-28"
        },
        json={"ref": branch, "inputs":{input_type: user_input}}
    )
    # Check the pipeline status
    status_code = response.status_code
    if status_code == 204:
        status_mess = f"Please wait a moment, currently running a workflow {workflow_id} on the {branch} by @{username} at {current_time}"
    else:
        status_mess = f"Error - Please double-check, the workflows with {workflow_id} is not active/correct"
    response = requests.post(f"https://api.telegram.org/bot{telegram_token}/sendMessage", data={"chat_id": chat_id, "text": status_mess})

    # Handle any errors in sending the message
    if response.status_code != 200:
        print(f"Error sending message: {response.status_code}")

# Function to lists all workflow runs for a repository
def list_task_run(chat_id, user_id):
    # Get the username from the user_id
    response = requests.get(f"https://api.telegram.org/bot{telegram_token}/getChat?chat_id={user_id}")

    # Trigger the pipeline
    response = requests.get(
        f"https://api.github.com/repos/xuongdon-iij/main/actions/runs",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {github_token}",
            "X-GitHub-Api-Version": "2022-11-28"
        }
    )
    # Initialize an empty list to store workflow runs information
    list_workflow_run = []

    # Check if the request was successful
    if response.status_code == 200:
        workflow_data = response.json()["workflow_runs"]
        for workflow_run in workflow_data:
            workflow_run_id = workflow_run["id"]
            workflow_run_name = workflow_run["name"]
            workflow_run_date = workflow_run["run_started_at"]
            workflow_run_status = workflow_run["status"]
            list_workflow_run.append(f"+ Workflow_Run_ID: {workflow_run_id} - Name: {workflow_run_name} - Status: {workflow_run_status} - Time: {workflow_run_date}\n------\n")
    else:
        list_workflow_run.append("Error: Unable to list to store workflow runs information")

    # Join the list of workflow information into a single string
    workflow_runs_information = "\n".join(list_workflow_run)

    # Send the message with the accumulated workflow information
    response = requests.post(f"https://api.telegram.org/bot{telegram_token}/sendMessage", data={"chat_id": chat_id, "text": workflow_runs_information})

    # Handle any errors in sending the message
    if response.status_code != 200:
        print(f"Error sending message: {response.status_code}")

def download_run_logs(chat_id, user_id, workflows_runs_id):
    # Get the username from the user_id
    response = requests.get(f"https://api.telegram.org/bot{telegram_token}/getChat?chat_id={user_id}")

    # Initialize file_log with a default value
    file_log = None

    # Trigger the pipeline
    response = requests.get(
        f"https://api.github.com/repos/xuongdon-iij/main/actions/runs/{workflows_runs_id}/logs",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {github_token}",
            "X-GitHub-Api-Version": "2022-11-28"
        }
    )
    # Check if the request was successful
    if response.status_code == 200:
        with open(f"./logs_{workflows_runs_id}.zip", "wb") as file:
            file.write(response.content)
        file_path = f"./logs_{workflows_runs_id}.zip"
        file_log = {"document": open(file_path, "rb")}
        download_log_text = f"This is a log files of Github Action workflow runs number: {workflows_runs_id}\nLink: https://github.com/xuongdon-iij/main/actions/runs/{workflows_runs_id}"
    else:
        download_log_text = f"Error - Unable to download an archive of log files - Please double-check, this workflow_run_id: {workflows_runs_id} invalid"
        
    requests.post(f"https://api.telegram.org/bot{telegram_token}/sendDocument", data={"chat_id": chat_id, "caption": download_log_text}, files=file_log)

def help_command(chat_id):
    help_text = "Available commands:\n"
    help_text += "/help - Show available commands\n"
    help_text += "/list workflow - List all Github Action workflow and show <Workflow ID>\n"
    help_text += "/run <branch> <Workflow ID> <Choice> - Run a workflow at branch\n"
    help_text += "/list log - List all logs of workflow runs and show <workflow_run_id>\n"
    help_text += "/download <workflow_run_id> - Download logs for a specific workflow run\n"
    requests.post(f"https://api.telegram.org/bot{telegram_token}/sendMessage", data={"chat_id": chat_id, "text": help_text})

# Function to get new updates
def get_updates(offset):
    response = requests.get(f"https://api.telegram.org/bot{telegram_token}/getUpdates?offset={offset}")
    return response.json()

offset = 0

while True:
    updates = get_updates(offset)
    message_count = len(updates.get("result", []))  # Use .get() with a default value

    if message_count > 0:
        for i in range(message_count):
            # Use .get() to access nested keys safely
            chat_id = updates["result"][i].get("message", {}).get("chat", {}).get("id")
            user_id = updates["result"][i].get("message", {}).get("from", {}).get("id")
            text = updates["result"][i].get("message", {}).get("text")

            if text:
                if text.startswith("/run "):
                    # Split the command text to extract branch and workflow_id
                    parts = text.split()
                    if len(parts) == 4 and parts[0] == "/run" and parts[1] == "main":
                        branch = parts[1]
                        workflow_id = parts[2]
                        user_input = parts[3]
                        # Check if workflow_id is a positive integer
                        if workflow_id.isdigit() and int(workflow_id) > 0 and user_input == "vCenter":
                            input_type = "Server"
                            run_workflow(chat_id, branch, user_id, workflow_id, input_type, user_input)
                        elif user_input == "production" or user_input == "staging":
                            input_type = "Environments"
                            run_workflow(chat_id, branch, user_id, workflow_id, input_type, user_input)
                        else:
                            response = requests.post(f"https://api.telegram.org/bot{telegram_token}/sendMessage", data={"chat_id": chat_id, "text": f"Error - Please double-check, <branch> or <Workflow ID> is not active/correct"})
                            # Handle any errors in sending the message
                            if response.status_code != 200:
                                print(f"Error sending message: {response.status_code}")
                    else:
                        response = requests.post(f"https://api.telegram.org/bot{telegram_token}/sendMessage", data={"chat_id": chat_id, "text": f"Error - Please double-check, <branch> or <Workflow ID> is not active/correct"})
                        # Handle any errors in sending the message
                        if response.status_code != 200:
                            print(f"Error sending message: {response.status_code}")
                elif text.startswith("/help"):
                    help_command(chat_id)
                elif text.startswith("/list ") and "workflow" in text.lower():
                    list_workflow(chat_id, user_id)
                elif text.startswith("/list ") and "log" in text.lower():
                    list_task_run(chat_id, user_id)
                elif text.startswith("/download "):
                    # Extract and validate workflows_runs_id from the command
                    parts = text.split()
                    if len(parts) == 2 and parts[0] == "/download":
                        workflows_runs_id = parts[1]
                        # Check if workflows_runs_id is a positive integer
                        if workflows_runs_id.isdigit() and int(workflows_runs_id) > 0:
                            download_run_logs(chat_id, user_id, workflows_runs_id)
                        else:
                            response = requests.post(f"https://api.telegram.org/bot{telegram_token}/sendMessage", data={"chat_id": chat_id, "text": help_command(chat_id)})
                            # Handle any errors in sending the message
                            if response.status_code != 200:
                                print(f"Error sending message: {response.status_code}")
                    else:
                        response = requests.post(f"https://api.telegram.org/bot{telegram_token}/sendMessage", data={"chat_id": chat_id, "text": help_command(chat_id)})
                        # Handle any errors in sending the message
                        if response.status_code != 200:
                            print(f"Error sending message: {response.status_code}")
                else:
                    # Handle incorrect command
                    response = requests.post(f"https://api.telegram.org/bot{telegram_token}/sendMessage", data={"chat_id": chat_id, "text": help_command(chat_id)})
                    # Handle any errors in sending the message
                    if response.status_code != 200:
                        print(f"Error sending message: {response.status_code}")

            update_id = updates["result"][i].get("update_id")
            offset = update_id + 1

    time.sleep(1)
