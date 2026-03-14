# AGENTS.md

This guide provides the necessary information for coding agents and developers working within the `K8sResourceResizer` repository.
It covers build, lint, and test commands; code style guidelines; and conventions to ensure consistency and high-quality code contributions.

---

## Build, Lint, and Test Commands

### Build Docker Image

To build the Docker image:
```bash
docker build --no-cache -t k8sresourceautoresizer -f Dockerfile .
```

### Run Tests

To execute the test suite:
```bash
pytest tests/
```

#### Run a Single Test

For a specific test file or test case:
```bash
pytest tests/test_file.py::SpecificTestCase
```

### Pre-commit Hooks
This repository uses pre-commit hooks to maintain code quality. Ensure hooks are installed and up to date:

#### Install Hooks

```bash
uv run prek install
```

#### Run All Hooks

```bash
uv run prek run --all-files
```

#### Update Hooks

```bash
uv run prek autoupdate
```

---

## Code Style Guidelines

The following conventions should be adhered to in all code contributions:

### Formatting

- Use `ruff` for linting and formatting checks:

  ```bash
  uv run ruff --fix
  ```

### Imports

- Group imports as follows (in order):
  1. Standard library imports
  2. Third-party library imports
  3. Local application/library imports
- Use absolute imports whenever possible.

### Types

- Python type hints are mandatory for all new code. For example:

  ```python
  def add(a: int, b: int) -> int:
      return a + b
  ```

- Use `mypy` for type checking.

### Naming Conventions

- **Functions**: Use `snake_case` (e.g., `calculate_metrics`).
- **Classes**: Use `PascalCase` (e.g., `ResourceOptimizer`).
- **Constants**: Use `UPPER_SNAKE_CASE` (e.g., `DEFAULT_CPU_LIMIT`).
- **Variables**: Use `lower_snake_case` (e.g., `resource_limits`).

### Error Handling

- Always catch specific exceptions:

  ```python
  try:
      risky_operation()
  except ValueError:
      handle_value_error()
  ```

- Avoid using bare exceptions (e.g., `except:`).
- Log meaningful information when exceptions occur using the `logger` module:

  ```python
  logger.error("An error occurred", exc_info=True)
  ```

### Logging

- Use the provided `logger` utility.
- Log debugging information with the `--debug` flag during development.

### Documentation

- Follow [Google-style docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings):

  ```python
  def fetch_data(source: str) -> dict:
      """Fetch data from a given source.

      Args:
          source (str): The source URL.

      Returns:
          dict: Parsed data.
      """
  ```

- Public methods and functions must include docstrings.

### File Organization

- Organize modules by functionality (e.g., `/strategy` contains optimization strategies).
- Place shared utilities in `/utils`.
- Avoid overly large files; refactor into smaller, logical components.

---

## Pre-commit Hooks

The following hooks are configured in `.pre-commit-config.yaml`:

- **Safety checks**:
  - `mixed-line-ending`: Ensures consistent line endings.
  - `trailing-whitespace`: Removes trailing whitespace.
  - `end-of-file-fixer`: Ensures files end with a newline.

- **Code quality**:
  - `ruff`: Lints Python files and autofixes issues.
  - `validate-pyproject`: Validates `pyproject.toml`.

- **Security checks**:
  - `detect-private-key`: Prevents private keys from being committed.

- **Commit message standardization**:
  - `commitizen`: Enforces conventional commit messages.

### Running Individual Hooks

To run a specific hook (e.g., `ruff`):

```bash
uv run prek run ruff
```

---

## Repository Conventions

### Branch Naming

- Use prefixes to categorize branch types:
  - `feat/*`: New features
  - `fix/*`: Bug fixes
  - `docs/*`: Documentation updates
  - `chore/*`: Maintenance tasks

### Commits

- Follow [Conventional Commits](https://www.conventionalcommits.org/):

  ```shell
  type(scope): description

  [optional body]
  [optional footer(s)]
  ```

  **Example:**

  ```shell
  feat(strategy): add support for trend-aware analysis

  Added new methods to analyze historical trends and usage patterns.
  ```

### Pull Requests

- Target the `main` branch.
- PR titles should reflect the changes (e.g., `Add support for quantile regression`).
- Include a description of the changes and test coverage information.

### Environment Configuration

- Copy `.env.example` to `.env` if required and populate the values.
- Example variables:
  - `AMP_WORKSPACE_ID`
  - `CLUSTER_NAME`
  - `GITHUB_TOKEN`

---

Following these guidelines will ensure that contributions remain structured and maintainable. Thank you for helping improve the `K8sResourceResizer` repository!
