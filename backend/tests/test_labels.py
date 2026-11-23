
from sqlalchemy import select

from app.models.label import Label, task_labels


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


def create_project(client, token, name="Label Test Project"):
    response = client.post(
        "/api/v1/projects/",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": name},
    )
    assert response.status_code == 201
    return response.json()["id"]


def create_task(client, token, project_id):
    response = client.post(
        f"/api/v1/projects/{project_id}/tasks/",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Label Test Task"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def create_label(client, token, project_id, name="BUG"):
    response = client.post(
        f"/api/v1/projects/{project_id}/labels/",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": name, "color": "#FF5733"},
    )
    assert response.status_code == 201
    return response.json()


def test_user_can_create_and_list_labels(client):
    token = register_and_login(client, "labelcreate@example.com")
    project_id = create_project(client, token)
    headers = {"Authorization": f"Bearer {token}"}

    create_label(client, token, project_id, "BUG")
    create_label(client, token, project_id, "URGENT")

    response = client.get(
        f"/api/v1/projects/{project_id}/labels/",
        headers=headers,
    )

    assert response.status_code == 200
    assert len(response.json()) == 2

    names = [label["name"] for label in response.json()]
    assert "BUG" in names
    assert "URGENT" in names


def test_duplicate_label_name_is_rejected(client):
    token = register_and_login(client, "labelduplicate@example.com")
    project_id = create_project(client, token)
    headers = {"Authorization": f"Bearer {token}"}

    create_label(client, token, project_id, "BUG")

    response = client.post(
        f"/api/v1/projects/{project_id}/labels/",
        headers=headers,
        json={"name": "BUG"},
    )

    assert response.status_code == 409


def test_same_label_name_allowed_in_different_projects(client):
    token = register_and_login(client, "labelprojects@example.com")

    project_one = create_project(client, token, "First Project")
    project_two = create_project(client, token, "Second Project")

    label_one = create_label(client, token, project_one, "BUG")
    label_two = create_label(client, token, project_two, "BUG")

    assert label_one["name"] == label_two["name"]
    assert label_one["id"] != label_two["id"]


def test_user_can_attach_label_to_task(client):
    token = register_and_login(client, "labelattach@example.com")
    project_id = create_project(client, token)
    task_id = create_task(client, token, project_id)
    label = create_label(client, token, project_id)

    response = client.post(
        f"/api/v1/projects/{project_id}/tasks/{task_id}/labels/{label['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == label["id"]


def test_attaching_same_label_twice_does_not_duplicate_it(
    client, db_session
):
    token = register_and_login(client, "labelduplicateattach@example.com")
    project_id = create_project(client, token)
    task_id = create_task(client, token, project_id)
    label = create_label(client, token, project_id)

    url = (
        f"/api/v1/projects/{project_id}/tasks/"
        f"{task_id}/labels/{label['id']}"
    )
    headers = {"Authorization": f"Bearer {token}"}

    first_response = client.post(url, headers=headers)
    second_response = client.post(url, headers=headers)

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    association = db_session.execute(
        select(task_labels).where(
            task_labels.c.task_id == task_id,
            task_labels.c.label_id == label["id"],
        )
    ).all()

    assert len(association) == 1


def test_user_can_remove_label_from_task(client, db_session):
    token = register_and_login(client, "labelremove@example.com")
    project_id = create_project(client, token)
    task_id = create_task(client, token, project_id)
    label = create_label(client, token, project_id)

    headers = {"Authorization": f"Bearer {token}"}

    attach_url = (
        f"/api/v1/projects/{project_id}/tasks/"
        f"{task_id}/labels/{label['id']}"
    )

    client.post(attach_url, headers=headers)

    response = client.delete(attach_url, headers=headers)

    assert response.status_code == 204

    association = db_session.execute(
        select(task_labels).where(
            task_labels.c.task_id == task_id,
            task_labels.c.label_id == label["id"],
        )
    ).first()

    assert association is None


def test_cannot_attach_label_from_another_project(client):
    token = register_and_login(client, "labelcrossproject@example.com")

    project_one = create_project(client, token, "Label Owner Project")
    project_two = create_project(client, token, "Task Owner Project")

    label = create_label(client, token, project_one, "PRIVATE")
    task_id = create_task(client, token, project_two)

    response = client.post(
        f"/api/v1/projects/{project_two}/tasks/"
        f"{task_id}/labels/{label['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404


def test_deleting_label_removes_task_association(client, db_session):
    token = register_and_login(client, "labeldelete@example.com")
    project_id = create_project(client, token)
    task_id = create_task(client, token, project_id)
    label = create_label(client, token, project_id)

    headers = {"Authorization": f"Bearer {token}"}

    attach_url = (
        f"/api/v1/projects/{project_id}/tasks/"
        f"{task_id}/labels/{label['id']}"
    )

    client.post(attach_url, headers=headers)

    response = client.delete(
        f"/api/v1/projects/{project_id}/labels/{label['id']}",
        headers=headers,
    )

    assert response.status_code == 204

    association = db_session.execute(
        select(task_labels).where(
            task_labels.c.task_id == task_id,
            task_labels.c.label_id == label["id"],
        )
    ).first()

    assert association is None

    deleted_label = db_session.query(Label).filter_by(
        id=label["id"]
    ).first()

    assert deleted_label is None
