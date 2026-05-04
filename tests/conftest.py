import os
from pathlib import Path

import pytest

from glenbog import create_app
from glenbog.extensions import db
from glenbog.models import User


_YAML_TEST_RESULTS = []


def pytest_sessionstart(session):
    _YAML_TEST_RESULTS.clear()


def pytest_runtest_logreport(report):
    if report.when != "call":
        return

    report_data = {
        "name": report.nodeid,
        "outcome": report.outcome,
        "duration": round(report.duration, 4),
    }
    if report.failed:
        report_data["message"] = str(report.longrepr).splitlines()[-1]

    _YAML_TEST_RESULTS.append(report_data)


def pytest_sessionfinish(session, exitstatus):
    results = _YAML_TEST_RESULTS
    total = len(results)
    passed = sum(1 for result in results if result["outcome"] == "passed")
    failed = sum(1 for result in results if result["outcome"] == "failed")
    skipped = sum(1 for result in results if result["outcome"] == "skipped")

    report_path = Path(os.getenv("TEST_REPORT_YML", "test-artifacts/report.yml"))
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        _to_simple_yaml({
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "exitstatus": exitstatus,
            },
            "tests": results,
        }),
        encoding="utf-8",
    )


def _to_simple_yaml(data, indent=0):
    lines = []
    prefix = " " * indent

    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                lines.append(f"{prefix}{key}:")
                lines.append(_to_simple_yaml(value, indent + 2))
            else:
                lines.append(f"{prefix}{key}: {_yaml_scalar(value)}")
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                lines.append(f"{prefix}-")
                lines.append(_to_simple_yaml(item, indent + 2))
            else:
                lines.append(f"{prefix}- {_yaml_scalar(item)}")

    return "\n".join(lines)


def _yaml_scalar(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)

    text = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{text}"'


@pytest.fixture
def app():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test-secret",
        "DATA_DIR": "/tmp",
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def test_user(app):
    with app.app_context():
        user = User(email="test@example.com")
        user.set_password("123")
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def logged_in_client(client, test_user):
    client.post("/login", data={
        "email": "test@example.com",
        "password": "123",
    })
    return client
