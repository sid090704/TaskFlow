def test_register_user(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "TestPassword123",
            "first_name": "Test",
            "last_name": "User",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == "newuser@example.com"
    assert data["first_name"] == "Test"
    assert "password" not in data
    assert "password_hash" not in data


def test_register_duplicate_email(client):
    payload = {
        "email": "duplicate@example.com",
        "password": "TestPassword123",
        "first_name": "Test",
        "last_name": "User",
    }

    first_response = client.post(
        "/api/v1/auth/register",
        json=payload,
    )

    second_response = client.post(
        "/api/v1/auth/register",
        json=payload,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_login_wrong_password(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "loginuser@example.com",
            "password": "CorrectPassword123",
            "first_name": "Login",
            "last_name": "User",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "loginuser@example.com",
            "password": "WrongPassword123",
        },
    )

    assert response.status_code == 401
    
    
    
def test_login_success(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "validuser@example.com",
            "password": "CorrectPassword123",
            "first_name": "Valid",
            "last_name": "User",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "validuser@example.com",
            "password": "CorrectPassword123",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
    

def test_get_my_profile(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "profileuser@example.com",
            "password": "CorrectPassword123",
            "first_name": "Profile",
            "last_name": "User",
        },
    )

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "profileuser@example.com",
            "password": "CorrectPassword123",
        },
    )

    token = login_response.json()["access_token"]

    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "profileuser@example.com"
    assert response.json()["first_name"] == "Profile"
    assert "password_hash" not in response.json()