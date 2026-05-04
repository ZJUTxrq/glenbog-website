from glenbog.extensions import db
from glenbog.models import User


def test_user_password_hashing(app):
    user = User(email="hash@example.com")
    user.set_password("123")

    assert user.password_hash != "123"
    assert user.check_password("123")
    assert not user.check_password("wrong")


def test_home_requires_login(client):
    response = client.get("/")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_register_rejects_invalid_code(client):
    response = client.post("/register", data={
        "email": "new@example.com",
        "password": "123",
        "password2": "123",
        "reg_code": "wrong",
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Invalid registration code" in response.data


def test_register_creates_user_with_valid_code(client, app):
    response = client.post("/register", data={
        "email": "new@example.com",
        "password": "123",
        "password2": "123",
        "reg_code": "ruqian_cactus",
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Registration successful" in response.data

    with app.app_context():
        user = User.query.filter_by(email="new@example.com").first()
        assert user is not None
        assert user.check_password("123")


def test_login_rejects_wrong_password(client, test_user):
    response = client.post("/login", data={
        "email": "test@example.com",
        "password": "wrong",
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Incorrect email or password" in response.data


def test_login_accepts_valid_password(client, test_user):
    response = client.post("/login", data={
        "email": "test@example.com",
        "password": "123",
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Logged in successfully" in response.data
    assert b"Navigation" in response.data


def test_logout_clears_session(logged_in_client):
    response = logged_in_client.get("/logout", follow_redirects=True)

    assert response.status_code == 200
    assert b"You have been logged out" in response.data
    assert b"Login" in response.data
