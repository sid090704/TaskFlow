
from datetime import datetime, timedelta, timezone

from app.models.activity_log import ActivityLog


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


def create_project(client, token, name="Test Project"):
    response = client.post(
        "/api/v1/projects/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": name,
            "description": "Project for activity log testing",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def create_activity(
    db_session,
    project_id,
    user_id,
    description="Test activity",
    created_at=None,
):
    activity = ActivityLog(
        project_id=project_id,
        user_id=user_id,
        action="TASK_CREATED",
        description=description,
        details={"task_title": "Test task"},
        created_at=created_at or datetime.now(timezone.utc),
    )

    db_session.add(activity)
    db_session.commit()
    db_session.refresh(activity)

    return activity


def get_user_id(client, token):
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    return response.json()["id"]


def test_project_member_can_list_activity_logs(client, db_session):
    token = register_and_login(client, "activity1@example.com")
    user_id = get_user_id(client, token)
    project_id = create_project(client, token)

    create_activity(db_session, project_id, user_id)
    create_activity(
        db_session,
        project_id,
        user_id,
        description="Another activity",
    )

    response = client.get(
        f"/api/v1/projects/{project_id}/activity-logs/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_activity_log_pagination(client, db_session):
    token = register_and_login(client, "activity2@example.com")
    user_id = get_user_id(client, token)
    project_id = create_project(client, token)

    base_time = datetime.now(timezone.utc)

    for i in range(3):
        create_activity(
            db_session,
            project_id,
            user_id,
            description=f"Activity {i + 1}",
            created_at=base_time + timedelta(seconds=i),
        )

    response = client.get(
        f"/api/v1/projects/{project_id}/activity-logs/?skip=0&limit=2",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["description"] == "Activity 3"
    assert response.json()[1]["description"] == "Activity 2"


def test_project_member_can_get_single_activity_log(
    client,
    db_session,
):
    token = register_and_login(client, "activity3@example.com")
    user_id = get_user_id(client, token)
    project_id = create_project(client, token)

    activity = create_activity(
        db_session,
        project_id,
        user_id,
        description="Task was created",
    )

    response = client.get(
        f"/api/v1/projects/{project_id}/activity-logs/{activity.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == activity.id
    assert response.json()["description"] == "Task was created"


def test_non_member_cannot_access_project_activity(
    client,
    db_session,
):
    owner_token = register_and_login(
        client,
        "activity4@example.com",
    )
    other_token = register_and_login(
        client,
        "activity5@example.com",
    )

    owner_id = get_user_id(client, owner_token)
    project_id = create_project(client, owner_token)

    create_activity(db_session, project_id, owner_id)

    response = client.get(
        f"/api/v1/projects/{project_id}/activity-logs/",
        headers={"Authorization": f"Bearer {other_token}"},
    )

    assert response.status_code == 404


def test_activity_log_cannot_be_accessed_through_another_project(
    client,
    db_session,
):
    token1 = register_and_login(client, "activity6@example.com")
    token2 = register_and_login(client, "activity7@example.com")

    user1_id = get_user_id(client, token1)

    project1_id = create_project(client, token1, "Project One")
    project2_id = create_project(client, token2, "Project Two")

    activity = create_activity(
        db_session,
        project1_id,
        user1_id,
    )

    response = client.get(
        f"/api/v1/projects/{project2_id}/activity-logs/{activity.id}",
        headers={"Authorization": f"Bearer {token2}"},
    )

    assert response.status_code == 404
