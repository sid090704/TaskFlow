
from app.models.project import Project
from app.models.project_member import ProjectMember, ProjectRole


def register_and_login(client):
    """Create a test user and return their access token."""

    client.post(
        "/api/v1/auth/register",
        json={
            "email": "projectuser@example.com",
            "password": "TestPassword123!",
            "first_name": "Project",
            "last_name": "User",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "projectuser@example.com",
            "password": "TestPassword123!",
        },
    )

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
