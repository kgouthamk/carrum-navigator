import os
import tomllib
from pathlib import Path
import pytest

SECRETS_PATH = Path(__file__).parent.parent / ".streamlit" / "secrets.toml"


def pytest_addoption(parser):
    parser.addoption(
        "--run-evals",
        action="store_true",
        default=False,
        help="Run LLM eval tests (requires GEMINI_API_KEY and burns API quota)",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "eval: LLM eval tests — skipped by default, enable with --run-evals or RUN_EVALS=1",
    )


@pytest.fixture(scope="session", autouse=True)
def load_secrets():
    """Load GEMINI_API_KEY / GEMINI_MODEL from secrets.toml if not already in env."""
    if not os.environ.get("GEMINI_API_KEY") and SECRETS_PATH.exists():
        with open(SECRETS_PATH, "rb") as f:
            secrets = tomllib.load(f)
        for key in ("GEMINI_API_KEY", "GEMINI_MODEL"):
            if key in secrets and not os.environ.get(key):
                os.environ[key] = str(secrets[key])


def pytest_collection_modifyitems(config, items):
    run_evals = config.getoption("--run-evals") or os.environ.get("RUN_EVALS") == "1"
    if not run_evals:
        skip = pytest.mark.skip(reason="LLM eval — pass --run-evals or set RUN_EVALS=1")
        for item in items:
            if "eval" in item.keywords:
                item.add_marker(skip)
