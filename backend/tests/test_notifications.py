
from app.models.notification import Notification


def create_notification(
    db_session,
    user_id,
    message="Test notification",
    is_read=False,
):
    notification = Notification(
        user_id=user_id,
        notification_type="TASK_ASSIGNED",
        message=message,
        is_read=is_read,
    )
    db_session.add(notification)
    db_session.commit()
    db_session.refresh(notification)
    return notification


def register_and_login(client, email):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123!",
            "first_name": "Test",
            "last_name": "User",
        },
    )
    assert response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "StrongPassword123!",
        },
    )
    assert login_response.status_code == 200

    return login_response.json()["access_token"]


def test_user_can_list_own_notifications(client, db_session):
    token = register_and_login(client, "notify1@example.com")

    user_id = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    ).json()["id"]

    create_notification(db_session, user_id)

    response = client.get(
        "/api/v1/notifications/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["message"] == "Test notification"


def test_user_cannot_see_another_users_notifications(
    client,
    db_session,
):
    token1 = register_and_login(client, "notify2@example.com")
    token2 = register_and_login(client, "notify3@example.com")

    user1_id = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token1}"},
    ).json()["id"]

    create_notification(db_session, user1_id)

    response = client.get(
        "/api/v1/notifications/",
        headers={"Authorization": f"Bearer {token2}"},
    )

    assert response.status_code == 200
    assert response.json() == []


def test_unread_filter(client, db_session):
    token = register_and_login(client, "notify4@example.com")

    user_id = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    ).json()["id"]

    create_notification(db_session, user_id, "Unread", False)
    create_notification(db_session, user_id, "Read", True)

    response = client.get(
        "/api/v1/notifications/?unread_only=true",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["message"] == "Unread"


def test_user_can_mark_notification_as_read(client, db_session):
    token = register_and_login(client, "notify5@example.com")

    user_id = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    ).json()["id"]

    notification = create_notification(db_session, user_id)

    response = client.patch(
        f"/api/v1/notifications/{notification.id}/read",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["is_read"] is True
    assert response.json()["read_at"] is not None


def test_user_cannot_mark_another_users_notification_as_read(
    client,
    db_session,
):
    token1 = register_and_login(client, "notify6@example.com")
    token2 = register_and_login(client, "notify7@example.com")

    user1_id = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token1}"},
    ).json()["id"]

    notification = create_notification(db_session, user1_id)

    response = client.patch(
        f"/api/v1/notifications/{notification.id}/read",
        headers={"Authorization": f"Bearer {token2}"},
    )

    assert response.status_code == 404


def test_mark_all_notifications_as_read(client, db_session):
    token = register_and_login(client, "notify8@example.com")

    user_id = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    ).json()["id"]

    create_notification(db_session, user_id, "Unread 1")
    create_notification(db_session, user_id, "Unread 2")
    create_notification(db_session, user_id, "Already read", True)

    response = client.patch(
        "/api/v1/notifications/read-all",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["updated_count"] == 2

    unread_response = client.get(
        "/api/v1/notifications/?unread_only=true",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert unread_response.json() == []
