
from app.models.project import Project
from app.models.project_member import ProjectMember, ProjectRole



def register_and_login(client, email="projectuser@example.com"):
    """Create a test user and return their access token."""

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "TestPassword123!",
            "first_name": "Project",
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



def test_authenticated_user_can_create_project(client, db_session):
    token = register_and_login(client)

    response = client.post(
        "/api/v1/projects/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "My First Project",
            "description": "A project created through the API",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "My First Project"
    assert data["description"] == "A project created through the API"

    project = db_session.query(Project).filter_by(id=data["id"]).first()

    assert project is not None

    membership = (
        db_session.query(ProjectMember)
        .filter_by(project_id=project.id)
        .first()
    )

    assert membership is not None
    assert membership.user_id == project.owner_id
    assert membership.role == ProjectRole.OWNER


def test_unauthenticated_user_cannot_create_project(client):
    response = client.post(
        "/api/v1/projects/",
        json={
            "name": "Unauthorized Project",
            "description": "This should not be created",
        },
    )

    assert response.status_code in (401, 403)


def test_project_name_must_have_at_least_three_characters(client):
    token = register_and_login(client)

    response = client.post(
        "/api/v1/projects/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "AB",
            "description": "Invalid project name",
        },
    )

    assert response.status_code == 422



def test_user_can_list_their_projects(client):
    token = register_and_login(client)

    headers = {"Authorization": f"Bearer {token}"}

    # Create the first project
    client.post(
        "/api/v1/projects/",
        headers=headers,
        json={"name": "Project Alpha"},
    )

    # Create the second project
    client.post(
        "/api/v1/projects/",
        headers=headers,
        json={"name": "Project Beta"},
    )

    response = client.get(
        "/api/v1/projects/",
        headers=headers,
    )

    assert response.status_code == 200
    assert len(response.json()) == 2

    project_names = [project["name"] for project in response.json()]

    assert "Project Alpha" in project_names
    assert "Project Beta" in project_names


def test_user_cannot_list_projects_without_authentication(client):
    response = client.get("/api/v1/projects/")

    assert response.status_code in (401, 403)



def test_user_cannot_view_another_users_project(client):
    owner_token = register_and_login(
        client, "owner@example.com"
    )

    outsider_token = register_and_login(
        client, "outsider@example.com"
    )

    # Owner creates a project
    create_response = client.post(
        "/api/v1/projects/",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "Private Project"},
    )

    project_id = create_response.json()["id"]

    # Another user tries to view it
    response = client.get(
        f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {outsider_token}"},
    )

    assert response.status_code == 404


def test_user_cannot_update_another_users_project(client):
    owner_token = register_and_login(
        client, "owner2@example.com"
    )

    outsider_token = register_and_login(
        client, "outsider2@example.com"
    )

    create_response = client.post(
        "/api/v1/projects/",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "Owner Project"},
    )

    project_id = create_response.json()["id"]

    response = client.patch(
        f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {outsider_token}"},
        json={"name": "Hacked Project"},
    )

    assert response.status_code == 404



def test_member_cannot_update_project(client, db_session):
    owner_token = register_and_login(
        client, "roleowner@example.com"
    )

    member_token = register_and_login(
        client, "rolemember@example.com"
    )

    # Owner creates a project
    create_response = client.post(
        "/api/v1/projects/",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "Team Project"},
    )

    project_id = create_response.json()["id"]

    # Add the second user as a MEMBER
    member_user_id = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {member_token}"},
    ).json()["id"]

    db_session.add(
        ProjectMember(
            project_id=project_id,
            user_id=member_user_id,
            role=ProjectRole.MEMBER,
        )
    )
    db_session.commit()

    # Member attempts to update the project
    response = client.patch(
        f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {member_token}"},
        json={"name": "Unauthorized Update"},
    )

    assert response.status_code == 403



def test_manager_cannot_delete_project(client, db_session):
    owner_token = register_and_login(
        client, "deleteowner@example.com"
    )

    manager_token = register_and_login(
        client, "deletemanager@example.com"
    )

    # Owner creates a project
    create_response = client.post(
        "/api/v1/projects/",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "Manager Test Project"},
    )

    project_id = create_response.json()["id"]

    # Get manager's user ID
    manager_user_id = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {manager_token}"},
    ).json()["id"]

    # Add manager membership
    db_session.add(
        ProjectMember(
            project_id=project_id,
            user_id=manager_user_id,
            role=ProjectRole.MANAGER,
        )
    )
    db_session.commit()

    # Manager attempts to delete project
    response = client.delete(
        f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {manager_token}"},
    )

    assert response.status_code == 403



def test_owner_can_update_project(client):
    token = register_and_login(client, "updateowner@example.com")

    headers = {"Authorization": f"Bearer {token}"}

    create_response = client.post(
        "/api/v1/projects/",
        headers=headers,
        json={
            "name": "Original Project",
            "description": "Original description",
        },
    )

    project_id = create_response.json()["id"]

    response = client.patch(
        f"/api/v1/projects/{project_id}",
        headers=headers,
        json={"name": "Updated Project"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Project"

    # Description must remain unchanged.
    assert response.json()["description"] == "Original description"



def test_deleting_project_also_deletes_memberships(client, db_session):
    token = register_and_login(
        client, "deletecascade@example.com"
    )

    headers = {"Authorization": f"Bearer {token}"}

    create_response = client.post(
        "/api/v1/projects/",
        headers=headers,
        json={"name": "Project To Delete"},
    )

    project_id = create_response.json()["id"]

    # Verify membership exists before deletion.
    membership = db_session.query(ProjectMember).filter_by(
        project_id=project_id
    ).first()

    assert membership is not None

    response = client.delete(
        f"/api/v1/projects/{project_id}",
        headers=headers,
    )

    assert response.status_code == 204

    # Verify membership was also deleted.
    membership = db_session.query(ProjectMember).filter_by(
        project_id=project_id
    ).first()

    assert membership is None
