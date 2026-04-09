import os
from dotenv import load_dotenv


def load_project_env():
    # Load .env from the repository root once so batch and UI runs work without manual exports.
    project_root = os.path.dirname(os.path.abspath(__file__))
    load_dotenv(os.path.join(project_root, ".env"), override=False)

