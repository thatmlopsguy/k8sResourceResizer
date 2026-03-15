from unittest.mock import MagicMock

from src import pr_opener


def test_create_github_pull_request_skips_on_no_commits(monkeypatch, caplog):
    # Ensure a token is present
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")

    # Mock Github and repository
    mock_g = MagicMock()
    mock_repo = MagicMock()

    comparison = MagicMock()
    comparison.total_commits = 0

    # repo.compare(base, head) should return an object with total_commits == 0
    mock_repo.compare.return_value = comparison
    mock_g.get_repo.return_value = mock_repo

    # Patch the Github constructor to return our mock
    monkeypatch.setattr(pr_opener, "Github", lambda token: mock_g)

    result = pr_opener.create_github_pull_request(
        repository_name="owner/repo",
        source_branch="feature-branch",
        destination_branch="main",
        title="Test PR",
        description="desc",
    )

    # Function should return None when there are no commits between branches
    assert result is None

    # Ensure we attempted to compare branches on the repository
    mock_repo.compare.assert_called_once_with("main", "feature-branch")
