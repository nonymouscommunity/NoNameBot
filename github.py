import git
import os
import json
from datetime import datetime
import time

# Function to clone or update a repository
# Function to clone or update a repository
def clone_or_update_repository(repo_url, repo_name):
    if os.path.exists(repo_name):
        try:
            repo = git.Repo(repo_name)
            origin = repo.remotes.origin

            # Check for uncommitted changes
            if repo.is_dirty():
                # Stash local changes
                repo.git.stash()

            origin.pull()

            # Optionally apply stashed changes if there were any
            if repo.git.stash("list"):
                repo.git.stash("pop")

        except git.GitCommandError as e:
            print(f"Error updating {repo_name}: {e}")
    else:
        try:
            repo = git.Repo.clone_from(repo_url, repo_name)
        except git.GitCommandError as e:
            print(f"Error cloning {repo_url} to {repo_name}: {e}")
            return

    # Get the last commit date
    last_commit = repo.head.commit.committed_date
    last_updated = datetime.fromtimestamp(last_commit)

    # Update the JSON file with the last update time
    data = read_json_file()
    data[repo_name] = last_updated.isoformat()
    write_json_file(data)

    if os.path.exists(repo_name):
        try:
            repo = git.Repo(repo_name)
            origin = repo.remotes.origin

            # Remove untracked files
            repo.git.clean("-f", "-d")

            origin.pull()
        except git.GitCommandError as e:
            print(f"Error updating {repo_name}: {e}")
    else:
        try:
            repo = git.Repo.clone_from(repo_url, repo_name)
        except git.GitCommandError as e:
            print(f"Error cloning {repo_url} to {repo_name}: {e}")
            return

    # Get the last commit date
    last_commit = repo.head.commit.committed_date
    last_updated = datetime.fromtimestamp(last_commit)

    # Update the JSON file with the last update time
    data = read_json_file()
    data[repo_name] = last_updated.isoformat()
    write_json_file(data)

# Function to read data from the JSON file
def read_json_file():
    try:
        with open('repos.json', 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        data = {}
    return data

# Function to write data to the JSON file
def write_json_file(data):
    with open('repos.json', 'w') as file:
        json.dump(data, file)

# List of repositories to monitor
repositories = [
    {'url': 'https://github.com/nonymouscommunity/NoName.git', 'name': 'NoName'}
]

# Create or load the JSON file
if not os.path.exists('repos.json'):
    with open('repos.json', 'w') as file:
        json.dump({}, file)

print("Repositories updated successfully.")


for repo_info in repositories:
    clone_or_update_repository(repo_info['url'], repo_info['name'])
