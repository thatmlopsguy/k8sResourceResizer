"""
Main entry point for the Kubernetes Resource Optimizer.

This module orchestrates the resource optimization process by:
1. Initializing the resource optimizer with AMP credentials
2. Generating resource recommendations based on usage metrics
3. Saving recommendations to a file for tracking
4. Processing deployments to update their resource configurations
"""

import json
import os
import secrets
import sys
import tempfile

import click
from dotenv import load_dotenv

from .argocd_client import apply_manifest
from .logger import setup_logger
from .manifest_updater import process_deployments
from .parser import get_applications_as_string
from .pr_opener import (
    clone_github_repo,
    commit_and_push_changes,
    create_and_switch_to_branch,
    create_github_pull_request,
)
from .prometheus_client import create_prometheus_client
from .resource_optimizer import ResourceOptimizer
from .strategy import RecommendationConfig, RecommendationStrategy, StrategyFactory
from .utils import handle_exceptions, parse_duration

# Load environment variables from .env file
load_dotenv()


@click.command()
@click.option(
    "--directory",
    default="tests/integration/helm",
    help="Directory containing YAML manifests. Default: tests/integration/kustomize",
)
@click.option(
    "--output",
    default=None,
    help="Path to save modified YAML. If not provided, a file will be created in a temporary TEMP directory",
)
@click.option(
    "--debug", is_flag=True, default=True, help="Enable debug mode. Default: True"
)
@click.option(
    "--strategy",
    type=click.Choice([s.value for s in RecommendationStrategy]),
    default=RecommendationStrategy.ENSEMBLE.value,
    help="Resource recommendation strategy to use",
)
@click.option(
    "--cpu-percentile",
    type=float,
    default=95.0,
    help="CPU percentile to use for recommendations",
)
@click.option(
    "--memory-buffer",
    type=float,
    default=1.15,
    help="Memory buffer multiplier (e.g., 1.15 for 15% buffer)",
)
@click.option(
    "--history-window",
    type=str,
    default="24h",
    help="Historical data window (e.g., 24h, 7d, 8w, 1yr). Default: 24h",
)
@click.option(
    "--prometheus-url",
    default=None,
    envvar="PROMETHEUS_URL",
    help="URL of the Prometheus-compatible endpoint.",
)
@click.option(
    "--prometheus-provider",
    type=click.Choice(["prometheus", "aws", "azure", "coralogix", "victoria_metrics"]),
    default="prometheus",
    envvar="PROMETHEUS_PROVIDER",
    help="Prometheus-compatible provider type. Default: prometheus",
)
@click.option(
    "--skip-pr",
    is_flag=True,
    help="Skip creating a GitHub pull request (useful for local runs)",
)
@handle_exceptions
def main(
    directory,
    output,
    debug,
    strategy,
    cpu_percentile,
    memory_buffer,
    history_window,
    prometheus_url,
    prometheus_provider,
    skip_pr,
):
    """Main function to run the resource optimization process."""
    logger = setup_logger(debug=debug)
    logger.info("Starting resource optimization process")

    # Parse history window
    try:
        history_hours = parse_duration(history_window)
        logger.info(f"Using historical data window of {history_hours} hours")
    except ValueError as e:
        logger.error(f"Invalid history window format: {e}")
        sys.exit(1)

    # Create temporary directory inside the project's `tmp` folder so runs
    # are colocated with the repository workspace (easier inspection).
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    project_tmp = os.path.join(repo_root, "tmp")
    try:
        os.makedirs(project_tmp, exist_ok=True)
    except Exception:
        project_tmp = None

    temp_base = (
        tempfile.mkdtemp(prefix="k8s_resource_", dir=project_tmp)
        if project_tmp
        else tempfile.mkdtemp(prefix="k8s_resource_")
    )
    temp_dir = os.path.join(temp_base, "TEMP")
    os.makedirs(temp_dir, exist_ok=True)

    # If user didn't provide an output path, write to TEMP/output.yaml
    if output is None:
        output = os.path.join(temp_dir, "output.yaml")
    else:
        out_dir = os.path.dirname(output)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

    # Create strategy configuration
    config = RecommendationConfig(
        strategy=RecommendationStrategy(strategy),
        cpu_percentile=cpu_percentile,
        memory_buffer=memory_buffer,
        business_hours_start=int(os.getenv("BUSINESS_HOURS_START", "9")),
        business_hours_end=int(os.getenv("BUSINESS_HOURS_END", "17")),
        business_days=[
            int(d) for d in os.getenv("BUSINESS_DAYS", "0,1,2,3,4").split(",")
        ],
        trend_threshold=float(os.getenv("TREND_THRESHOLD", "0.1")),
        high_variance_threshold=float(os.getenv("HIGH_VARIANCE_THRESHOLD", "0.5")),
        history_window_hours=history_hours,
    )

    strategy_instance = StrategyFactory.create_strategy(config)
    logger.info(f"Using {strategy} strategy for recommendations")

    # Get modified YAML
    modified_yaml = get_applications_as_string(directory)

    # Write to TEMP/output.yaml
    with open(output, "w") as f:
        f.write(modified_yaml)
    logger.info(f"Modified YAML saved to: {output}")

    # Apply the manifest
    logger.info(f"Applying the manifest: {output}")
    apply_manifest(output)

    # Initialize the Prometheus client
    prom_client = None
    if prometheus_url:
        prom_kwargs: dict = {}
        if prometheus_provider == "aws":
            aws_region = os.getenv("AWS_REGION", "us-east-1")
            prom_kwargs["aws_region"] = aws_region
        prom_client = create_prometheus_client(
            url=prometheus_url,
            provider=prometheus_provider,
            **prom_kwargs,
        )
        logger.info(f"Prometheus client initialized (provider={prometheus_provider})")
    else:
        logger.warning("No --prometheus-url supplied; metrics queries will be skipped")

    # Initialize the resource optimizer with strategy
    optimizer = ResourceOptimizer(
        strategy=strategy_instance,
        prometheus_client=prom_client,
    )

    # Generate recommendations
    recommendations = optimizer.generate_recommendations()

    # Prepare for PR automation: if we have GitHub credentials and are
    # not skipping PRs, clone the target repository and create a new
    # branch so subsequent manifest updates are written directly into
    # the cloned branch (in `tmp`) instead of the tool's working tree.
    github_username = os.getenv("GITHUB_USERNAME")
    repo_name = os.getenv("GITHUB_REPOSITORY_NAME")
    github_token = os.environ.get("GITHUB_TOKEN")

    pr_clone_dir = None
    new_branch_name = None

    if not skip_pr and github_token and github_username and repo_name:
        repo_url = (
            f"https://{github_token}@github.com/{github_username}/{repo_name}.git"
        )
        cloned_path = clone_github_repo(repo_url)
        if cloned_path:
            pr_clone_dir = cloned_path
            random_number = secrets.randbelow(1000) + 1
            new_branch_name = f"update_resources_k8s_manifests_{random_number}"
            created = create_and_switch_to_branch(pr_clone_dir, new_branch_name)
            if not created:
                logger.error(
                    "Failed to create branch in cloned repo; will update local files instead"
                )
                pr_clone_dir = None
        else:
            logger.error(
                "Failed to clone repo for PR automation; will update local files instead"
            )

    # Determine target directory for manifest updates. If we cloned the
    # repository for PR automation, write updates into the cloned repo so
    # they end up on the feature branch; otherwise update the provided
    # `directory` in-place (useful for --skip-pr or missing credentials).
    target_directory = directory
    if pr_clone_dir:
        # If `directory` is an absolute path inside this workspace, try to
        # convert it to a repo-relative path. Otherwise join directly.
        if os.path.isabs(directory):
            repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            try:
                rel_dir = os.path.relpath(directory, start=repo_root)
                target_directory = os.path.join(pr_clone_dir, rel_dir)
            except Exception:
                target_directory = os.path.join(pr_clone_dir, directory)
        else:
            target_directory = os.path.join(pr_clone_dir, directory)

    # Process deployments and get updated deployments
    updated_deployments = process_deployments(recommendations, target_directory)
    logger.info(f"Updated {len(updated_deployments)} deployments")

    # Prepare recommendations data structure
    logger.info("Preparing recommendations data structure")
    recommendations_data = optimizer.prepare_recommendations_to_save(
        recommendations, updated_deployments
    )

    # Save recommendations to file
    logger.info(f"Using TEMP directory: {temp_dir}")
    os.makedirs(temp_dir, exist_ok=True)
    with open(os.path.join(temp_dir, "recommendations.json"), "w") as f:
        json.dump(recommendations_data, f, indent=2)

    logger.info("Resource optimization process completed")
    logger.info("Starting automated process to create pull request ...")

    # If no deployments were updated, there's nothing to commit or PR.
    if not updated_deployments:
        logger.info("No deployments were updated; skipping PR automation.")
        return

    repository_full_name = None
    if skip_pr:
        logger.info("Skipping PR automation because --skip-pr was provided")
        return

    if not (github_token and github_username and repo_name):
        logger.warning(
            "Missing GitHub credentials; cannot create PR. Set GITHUB_TOKEN, GITHUB_USERNAME and GITHUB_REPOSITORY_NAME."
        )
        return

    repository_full_name = f"{github_username}/{repo_name}"
    repo_url = f"https://{github_token}@github.com/{github_username}/{repo_name}.git"

    # Commit and push from cloned branch if available, otherwise fall back
    if pr_clone_dir and new_branch_name:
        commit_and_push_changes(
            recommendations_data, pr_clone_dir, new_branch_name, repo_url
        )
        source_branch = new_branch_name
    else:
        # Fallback: commit from the workspace (not ideal for PRs)
        workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        commit_and_push_changes(recommendations_data, workspace_root, "main", repo_url)
        source_branch = "main"

    destination_branch = "main"
    title = "K8s manifest resource usage updates, please take a look and update with the following recommendations"
    description = (
        "This PR was automatically generated by the Kubernetes Resource Optimizer tool. "
        "It includes recommendations for updating resource requests and limits based on recent usage metrics. "
        "Please review the changes and merge if they look good."
    )

    create_github_pull_request(
        repository_full_name,
        source_branch,
        destination_branch,
        title,
        description=description,
    )
    logger.info("Automation process finished successfully")


if __name__ == "__main__":
    main()
