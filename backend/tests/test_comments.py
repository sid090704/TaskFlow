
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
        json={"name": "Comment Test Project"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def create_task(client, token, project_id):
    response = client.post(
        f"/api/v1/projects/{project_id}/tasks/",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Comment Test Task"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def create_comment(client, token, project_id, task_id):
    response = client.post(
        f"/api/v1/projects/{project_id}/tasks/{task_id}/comments/",
        headers={"Authorization": f"Bearer {token}"},
        json={"content": "This is a test comment"},
    )
    assert response.status_code == 201
    return response.json()


def test_user_can_create_comment(client):
    token = register_and_login(client, "commentcreate@example.com")
    project_id = create_project(client, token)
    task_id = create_task(client, token, project_id)

    comment = create_comment(client, token, project_id, task_id)

    assert comment["content"] == "This is a test comment"
    assert comment["task_id"] == task_id


def test_user_can_list_comments(client):
    token = register_and_login(client, "commentlist@example.com")
    project_id = create_project(client, token)
    task_id = create_task(client, token, project_id)

    create_comment(client, token, project_id, task_id)

    response = client.get(
        f"/api/v1/projects/{project_id}/tasks/{task_id}/comments/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_user_can_update_own_comment(client):
    token = register_and_login(client, "commentupdate@example.com")
    project_id = create_project(client, token)
    task_id = create_task(client, token, project_id)

    comment = create_comment(client, token, project_id, task_id)

    response = client.patch(
        f"/api/v1/projects/{project_id}/tasks/{task_id}/comments/{comment['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={"content": "Updated comment"},
    )

    assert response.status_code == 200
    assert response.json()["content"] == "Updated comment"


def test_user_can_delete_own_comment(client):
    token = register_and_login(client, "commentdelete@example.com")
    project_id = create_project(client, token)
    task_id = create_task(client, token, project_id)

    comment = create_comment(client, token, project_id, task_id)

    response = client.delete(
        f"/api/v1/projects/{project_id}/tasks/{task_id}/comments/{comment['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 204


def test_user_cannot_edit_another_users_comment(client, db_session):
    owner_token = register_and_login(
        client, "commentowner@example.com"
    )
    member_token = register_and_login(
        client, "commentmember@example.com"
    )

    project_id = create_project(client, owner_token)
    task_id = create_task(client, owner_token, project_id)

    # Add the second user to the project.
    member_id = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {member_token}"},
    ).json()["id"]

    from app.models.project_member import ProjectMember, ProjectRole

    db_session.add(
        ProjectMember(
            project_id=project_id,
            user_id=member_id,
            role=ProjectRole.MEMBER,
        )
    )
    db_session.commit()

    comment = create_comment(
        client, owner_token, project_id, task_id
    )

    response = client.patch(
        f"/api/v1/projects/{project_id}/tasks/{task_id}/comments/{comment['id']}",
        headers={"Authorization": f"Bearer {member_token}"},
        json={"content": "Trying to edit someone else's comment"},
    )

    assert response.status_code == 403
