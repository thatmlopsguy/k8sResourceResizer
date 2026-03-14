import os

# import boto3
import subprocess
from github import Github
from git import Repo, GitCommandError
from logger import logger
import shutil


def invoke_bedrock_model(prompt, region):
    """
    Invoke the bedrock model to generate the pull request description
    """
    # brt = boto3.client(service_name="bedrock-runtime", region_name=region)

    # Construct the request parameters if using Bedrock/Claude (kept for reference)
    # Note: the actual invocation is currently disabled; uncomment and adapt
    # when the Bedrock client is configured.
    # request_payload = {
    #     "anthropic_version": "bedrock-2023-05-31",
    #     "max_tokens": 10000,
    #     "temperature": 0.5,
    #     "top_p": 0.9,
    #     "messages": [{"role": "user", "content": prompt}],
    # }

    # Example model and headers (kept as reference)
    # model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
    # headers = {"Accept": "application/json", "Content-Type": "application/json"}

    # Example invocation (disabled):
    # response = brt.invoke_model(body=json.dumps(request_payload), modelId=model_id, accept=headers["Accept"], contentType=headers["Content-Type"])

    # If/when re-enabled, parse response as needed and return the generated text.


def delete_local_repo(local_dir):
    """
    Delete local directory of the repository if already exists
    """
    if os.path.exists(local_dir):
        # Use shutil instead of os.system/subprocess for directory removal
        shutil.rmtree(local_dir, ignore_errors=True)


def create_github_pull_request(
    repository_name, source_branch, destination_branch, title, description
):
    """
    Create pull request based on the new remote branch pushed
    """
    # Use the GitHub token from environment variables
    github_token = os.environ.get("GIT_TOKEN")
    if not github_token:
        raise ValueError("GITHUB_TOKEN environment variable is not set")

    g = Github(github_token)

    try:
        # Get the repository
        repo = g.get_repo(repository_name)

        # Create the pull request
        pr = repo.create_pull(
            title=title, body=description, head=source_branch, base=destination_branch
        )

        logger.info(f"Pull Request Created: {pr.html_url}")
        return pr.number
    except Exception as e:
        logger.info(f"Error creating pull request: {e}")
        return None


def clone_github_repo(repo_url, local_dir):
    """
    Clone remote repository with manifests
    """
    try:
        # Ensure the target directory doesn't exist
        if os.path.exists(local_dir):
            logger.info(f"Directory {local_dir} already exists. Removing it.")
            shutil.rmtree(
                local_dir, ignore_errors=True
            )  # Use shutil instead of subprocess

        git_bin = "/usr/bin/git"

        # Clone the repository using full path
        subprocess.run(
            [git_bin, "clone", repo_url, local_dir],
            check=True,
            capture_output=True,
            text=True,
            shell=False,
        )

        logger.info(f"Repository successfully cloned into {local_dir}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error cloning the repository: {e.stderr}")
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        raise


def create_and_switch_to_branch(repo_path, new_branch_name):
    """
    Create a new branch and switch to it locally to prepare for the pull request
    """
    try:
        repo = Repo(repo_path)

        new_branch = repo.create_head(new_branch_name)
        new_branch.checkout()

        logger.info(f"Branch '{new_branch_name}' created.")
        return True
    except GitCommandError as e:
        logger.info(f"Error creating branch {new_branch_name}: {e}")
        return False
    except Exception as e:
        logger.info(f"Unknown error: {e}")
        return False


def commit_and_push_changes(recommendations, local_dir, branch_name, repo_url):
    """
    Commit and push all the changes to the new branch of the repository
    """
    # Initialize Git repository
    repo = Repo(local_dir)

    # Set up the remote URL with your GitHub token
    remote_url = repo_url
    origin = repo.remote("origin")
    origin.set_url(remote_url)

    # Set user name and email for Git commit
    repo.config_writer().set_value("user", "name", "Resource Updater").release()
    repo.config_writer().set_value(
        "user", "email", "resource_updater@example.com"
    ).release()

    # helper functions available in prompt_creator are intentionally not used here
    # but may be useful for callers that need the file lists/contents.

    for deployment in recommendations["metadata"]["updated_deployments"]:
        values_file_path_relative = deployment["updated_file"].split(
            "/app/manifests/", 1
        )[1]
        # Directly copy the file content without YAML parsing
        shutil.copy2(
            deployment["updated_file"], f"{local_dir}/{values_file_path_relative}"
        )

        # Commit changes
        repo.git.add(values_file_path_relative)
        repo.git.commit("-m", "Updating values with recommendations")

    # Push the new branch (optional, may require additional authentication setup)
    repo.git.push("origin", branch_name)

    logger.info(f"values.yaml updated on branch '{branch_name}'.")
    return True
