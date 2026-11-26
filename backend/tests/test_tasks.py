
from app.models.task import Task, TaskStatus, TaskPriority
from app.models.project_member import ProjectMember, ProjectRole
from app.models.activity_log import ActivityLog
from app.models.notification import Notification

def register_and_login(client, email):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "TestPassword123!",
            "first_name": "Test",
            "last_name": "User",
        },
    )
    assert response.status_code == 201

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "TestPassword123!",
        },
    )
    assert response.status_code == 200

    return response.json()["access_token"]


def create_project(client, token):
    response = client.post(
        "/api/v1/projects/",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Task Test Project"},
    )

    assert response.status_code == 201
    return response.json()["id"]


def create_task(client, token, project_id, title="Test Task"):
    response = client.post(
        f"/api/v1/projects/{project_id}/tasks/",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": title},
    )

    assert response.status_code == 201
    return response.json()


def test_user_can_create_task(client):
    token = register_and_login(client, "taskcreate@example.com")
    project_id = create_project(client, token)

    task = create_task(client, token, project_id)

    assert task["title"] == "Test Task"
    assert task["status"] == "TODO"
    assert task["priority"] == "MEDIUM"
    assert task["creator_id"] is not None


def test_user_can_list_project_tasks(client):
    token = register_and_login(client, "tasklist@example.com")
    project_id = create_project(client, token)

    create_task(client, token, project_id, "Task One")
    create_task(client, token, project_id, "Task Two")

    response = client.get(
        f"/api/v1/projects/{project_id}/tasks/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_user_can_filter_tasks_by_status(client):
    token = register_and_login(client, "taskfilter@example.com")
    project_id = create_project(client, token)

    task = create_task(client, token, project_id)

    client.patch(
        f"/api/v1/projects/{project_id}/tasks/{task['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "DONE"},
    )

    response = client.get(
        f"/api/v1/projects/{project_id}/tasks/?status_filter=DONE",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["status"] == "DONE"


def test_user_can_update_task(client):
    token = register_and_login(client, "taskupdate@example.com")
    project_id = create_project(client, token)
    task = create_task(client, token, project_id)

    response = client.patch(
        f"/api/v1/projects/{project_id}/tasks/{task['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={"priority": "URGENT"},
    )

    assert response.status_code == 200
    assert response.json()["priority"] == "URGENT"


def test_completing_task_sets_completed_at(client):
    token = register_and_login(client, "taskcomplete@example.com")
    project_id = create_project(client, token)
    task = create_task(client, token, project_id)

    response = client.patch(
        f"/api/v1/projects/{project_id}/tasks/{task['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "DONE"},
    )

    assert response.status_code == 200
    assert response.json()["completed_at"] is not None


def test_reopening_task_clears_completed_at(client):
    token = register_and_login(client, "taskreopen@example.com")
    project_id = create_project(client, token)
    task = create_task(client, token, project_id)

    headers = {"Authorization": f"Bearer {token}"}
    task_url = f"/api/v1/projects/{project_id}/tasks/{task['id']}"

    client.patch(task_url, headers=headers, json={"status": "DONE"})

    response = client.patch(
        task_url,
        headers=headers,
        json={"status": "IN_PROGRESS"},
    )

    assert response.status_code == 200
    assert response.json()["completed_at"] is None


def test_user_cannot_assign_task_to_non_member(client):
    token = register_and_login(client, "taskassignowner@example.com")
    outsider_token = register_and_login(
        client, "taskassignoutsider@example.com"
    )

    project_id = create_project(client, token)
    task = create_task(client, token, project_id)

    outsider_id = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {outsider_token}"},
    ).json()["id"]

    response = client.patch(
        f"/api/v1/projects/{project_id}/tasks/{task['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={"assignee_id": outsider_id},
    )

    assert response.status_code == 400


def test_user_cannot_access_another_projects_task(client):
    owner_token = register_and_login(
        client, "taskprojectowner@example.com"
    )
    outsider_token = register_and_login(
        client, "taskprojectoutsider@example.com"
    )

    project_id = create_project(client, owner_token)
    task = create_task(client, owner_token, project_id)

    # The outsider creates a separate project.
    outsider_project_id = create_project(client, outsider_token)

    response = client.get(
        f"/api/v1/projects/{outsider_project_id}/tasks/{task['id']}",
        headers={"Authorization": f"Bearer {outsider_token}"},
    )

    assert response.status_code == 404


def test_owner_can_delete_task(client):
    token = register_and_login(client, "taskdeleteowner@example.com")
    project_id = create_project(client, token)
    task = create_task(client, token, project_id)

    headers = {"Authorization": f"Bearer {token}"}

    response = client.delete(
        f"/api/v1/projects/{project_id}/tasks/{task['id']}",
        headers=headers,
    )

    assert response.status_code == 204

    get_response = client.get(
        f"/api/v1/projects/{project_id}/tasks/{task['id']}",
        headers=headers,
    )

    assert get_response.status_code == 404


def test_member_cannot_delete_task(client, db_session):
    owner_token = register_and_login(
        client, "taskdeletememberowner@example.com"
    )
    member_token = register_and_login(
        client, "taskdeletemember@example.com"
    )

    project_id = create_project(client, owner_token)
    task = create_task(client, owner_token, project_id)

    member_id = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {member_token}"},
    ).json()["id"]

    db_session.add(
        ProjectMember(
            project_id=project_id,
            user_id=member_id,
            role=ProjectRole.MEMBER,
        )
    )
    db_session.commit()

    response = client.delete(
        f"/api/v1/projects/{project_id}/tasks/{task['id']}",
        headers={"Authorization": f"Bearer {member_token}"},
    )

    assert response.status_code == 403


def test_task_creation_generates_activity_log(client, db_session):
    token = register_and_login(client, "taskactivity@example.com")
    project_id = create_project(client, token)

    task = create_task(client, token, project_id)

    activity = db_session.query(ActivityLog).filter(
        ActivityLog.task_id == task["id"],
        ActivityLog.action == "TASK_CREATED",
    ).first()

    assert activity is not None
    assert activity.project_id == project_id
    assert activity.description == f'Created task "{task["title"]}"'

    # An unassigned task should not generate a notification.
    notification_count = db_session.query(Notification).filter(
        Notification.task_id == task["id"],
    ).count()

    assert notification_count == 0


def test_task_assignment_generates_notification(
    client,
    db_session,
):
    owner_token = register_and_login(
        client, "tasknotifyowner@example.com"
    )
    member_token = register_and_login(
        client, "tasknotifymember@example.com"
    )

    project_id = create_project(client, owner_token)

    member_id = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {member_token}"},
    ).json()["id"]

    owner_id = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {owner_token}"},
    ).json()["id"]

    # Add the second user to the project.
    db_session.add(
        ProjectMember(
            project_id=project_id,
            user_id=member_id,
            role=ProjectRole.MEMBER,
        )
    )
    db_session.commit()

    response = client.post(
        f"/api/v1/projects/{project_id}/tasks/",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "title": "Build login API",
            "priority": "HIGH",
            "assignee_id": member_id,
        },
    )

    assert response.status_code == 201
    task = response.json()

    # Verify activity creation.
    activity = db_session.query(ActivityLog).filter(
        ActivityLog.task_id == task["id"],
        ActivityLog.action == "TASK_CREATED",
    ).first()

    assert activity is not None
    assert activity.user_id == owner_id

    # Verify notification creation for the assigned member.
    notification = db_session.query(Notification).filter(
        Notification.user_id == member_id,
        Notification.task_id == task["id"],
        Notification.notification_type == "TASK_ASSIGNED",
    ).first()

    assert notification is not None
    assert notification.actor_id == owner_id
    assert notification.is_read is False
    assert "Build login API" in notification.message


def test_assigning_task_to_self_does_not_generate_notification(
    client,
    db_session,
):
    token = register_and_login(
        client, "taskselfassign@example.com"
    )
    project_id = create_project(client, token)

    user_id = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    ).json()["id"]

    response = client.post(
        f"/api/v1/projects/{project_id}/tasks/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "My own task",
            "assignee_id": user_id,
        },
    )

    assert response.status_code == 201
    task = response.json()

    activity = db_session.query(ActivityLog).filter(
        ActivityLog.task_id == task["id"],
        ActivityLog.action == "TASK_CREATED",
    ).first()

    assert activity is not None

    notification_count = db_session.query(Notification).filter(
        Notification.task_id == task["id"],
    ).count()

    assert notification_count == 0
