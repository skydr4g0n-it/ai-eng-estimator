from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_required_project_structure_exists() -> None:
    required_paths = [
        "app/__init__.py",
        "app/main.py",
        "app/config.py",
        "app/dependencies.py",
        "app/routers/__init__.py",
        "app/routers/estimations.py",
        "app/schemas/__init__.py",
        "app/schemas/estimation.py",
        "app/services/__init__.py",
        "app/services/llm_service.py",
        "app/services/cache.py",
        "app/services/llm_wrapper.py",
        "app/services/evaluation.py",
        "app/context/__init__.py",
        "app/context/examples.py",
        "app/static/sse_demo.html",
        ".env.example",
        ".gitignore",
        ".dockerignore",
        "Dockerfile",
        "docker-compose.yml",
        "pyproject.toml",
        "README.md",
        "transcripts/meeting_transcription.txt",
    ]

    missing_paths = [path for path in required_paths if not (PROJECT_ROOT / path).exists()]

    assert missing_paths == []


def test_env_file_is_ignored_by_git() -> None:
    gitignore = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")

    assert ".env" in gitignore.splitlines()


def test_project_is_named_estimator() -> None:
    pyproject = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert 'name = "Estimator"' in pyproject


def test_docker_configuration_runs_app_and_tests() -> None:
    dockerfile = (PROJECT_ROOT / "Dockerfile").read_text(encoding="utf-8")
    compose = (PROJECT_ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert "uvicorn" in dockerfile
    assert "app.main:app" in dockerfile
    assert "redis:" in compose
    assert "api:" in compose
    assert "tests:" in compose
    assert "pytest" in compose
