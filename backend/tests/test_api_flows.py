from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient
def register(client: TestClient, created_users: list[int], *, name: str = "QA Tester") -> dict:
    suffix = uuid4().hex[:10]
    response = client.post(
        "/api/v1/auth/register",
        json={
            "name": name,
            "username": f"qa_{suffix}",
            "email": f"qa_{suffix}@teamflow.dev",
            "password": "secret123",
        },
    )
    assert response.status_code == 201, response.text
    payload = response.json()
    created_users.append(payload["user"]["id"])
    return payload


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def default_workspace_and_board(client: TestClient, token: str) -> tuple[dict, dict]:
    headers = auth_headers(token)
    workspaces = client.get("/api/v1/workspaces", headers=headers)
    assert workspaces.status_code == 200, workspaces.text
    workspace = next(item for item in workspaces.json() if item["name"] == "Основное")
    boards = client.get(f"/api/v1/workspaces/{workspace['id']}/boards", headers=headers)
    assert boards.status_code == 200, boards.text
    return workspace, boards.json()[0]


def test_registration_creates_username_and_default_workspace(client, created_users):
    payload = register(client, created_users, name="Default Workspace User")
    assert payload["user"]["username"].startswith("qa_")

    workspace, board = default_workspace_and_board(client, payload["access_token"])
    assert workspace["name"] == "Основное"
    assert board["title"] == "Моя первая доска"
    assert board["is_archived"] is False


def test_board_owner_can_rename_board(client, created_users):
    owner = register(client, created_users, name="Board Rename Owner")
    workspace, board = default_workspace_and_board(client, owner["access_token"])
    response = client.patch(
        f"/api/v1/workspaces/{workspace['id']}/boards/{board['id']}",
        headers=auth_headers(owner["access_token"]),
        json={"title": "План релиза"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["title"] == "План релиза"
    assert response.json()["can_edit"] is True


def test_board_invitation_code_claim_and_notification(client, created_users):
    owner = register(client, created_users, name="Board Owner")
    guest = register(client, created_users, name="Board Guest")
    workspace, board = default_workspace_and_board(client, owner["access_token"])

    invitation_response = client.post(
        f"/api/v1/boards/{board['id']}/invitations",
        headers=auth_headers(owner["access_token"]),
        json={},
    )
    assert invitation_response.status_code == 201, invitation_response.text
    invitation = invitation_response.json()
    assert len(invitation["code"]) == 8
    assert invitation["invitee_id"] is None
    assert invitation["status"] == "pending"

    claim_response = client.post(
        "/api/v1/invitations/claim",
        headers=auth_headers(guest["access_token"]),
        json={"code": invitation["code"]},
    )
    assert claim_response.status_code == 200, claim_response.text
    assert claim_response.json()["status"] == "accepted"
    assert claim_response.json()["invitee_id"] == guest["user"]["id"]

    guest_workspaces = client.get("/api/v1/workspaces", headers=auth_headers(guest["access_token"]))
    assert guest_workspaces.status_code == 200, guest_workspaces.text
    assert all(item["id"] != workspace["id"] for item in guest_workspaces.json())

    guest_boards = client.get("/api/v1/boards", headers=auth_headers(guest["access_token"]))
    assert guest_boards.status_code == 200, guest_boards.text
    assert any(item["id"] == board["id"] for item in guest_boards.json())

    notifications = client.get("/api/v1/notifications", headers=auth_headers(owner["access_token"]))
    assert notifications.status_code == 200, notifications.text
    assert any(item["kind"] == "board_invitation_accepted" and item["board_id"] == board["id"] for item in notifications.json())


def test_username_invitation_creates_notification(client, created_users):
    owner = register(client, created_users, name="Username Owner")
    guest = register(client, created_users, name="Username Guest")
    _, board = default_workspace_and_board(client, owner["access_token"])

    response = client.post(
        f"/api/v1/boards/{board['id']}/invitations",
        headers=auth_headers(owner["access_token"]),
        json={"username": guest["user"]["username"]},
    )
    assert response.status_code == 201, response.text
    assert response.json()["invitee_id"] == guest["user"]["id"]

    notifications = client.get("/api/v1/notifications", headers=auth_headers(guest["access_token"]))
    assert notifications.status_code == 200, notifications.text
    assert any(item["kind"] == "board_invitation" and item["board_id"] == board["id"] for item in notifications.json())


def test_task_comments_delete_and_move_notify_board_members(client, created_users):
    owner = register(client, created_users, name="Task Owner")
    guest = register(client, created_users, name="Task Guest")
    workspace, board = default_workspace_and_board(client, owner["access_token"])
    owner_headers = auth_headers(owner["access_token"])
    guest_headers = auth_headers(guest["access_token"])

    invitation = client.post(
        f"/api/v1/boards/{board['id']}/invitations",
        headers=owner_headers,
        json={},
    ).json()
    claim = client.post("/api/v1/invitations/claim", headers=guest_headers, json={"code": invitation["code"]})
    assert claim.status_code == 200, claim.text

    details = client.get(f"/api/v1/workspaces/{workspace['id']}/boards/{board['id']}", headers=owner_headers)
    assert details.status_code == 200, details.text
    columns = details.json()["columns"]
    task_response = client.post(
        "/api/v1/tasks",
        headers=owner_headers,
        json={"column_id": columns[0]["id"], "title": "Проверить релиз", "description": "", "priority": "medium"},
    )
    assert task_response.status_code == 201, task_response.text
    task_id = task_response.json()["id"]

    moved = client.patch(
        f"/api/v1/tasks/{task_id}",
        headers=guest_headers,
        json={"column_id": columns[1]["id"]},
    )
    assert moved.status_code == 200, moved.text

    comment = client.post(
        f"/api/v1/tasks/{task_id}/comments",
        headers=guest_headers,
        json={"text": "Готово к проверке"},
    )
    assert comment.status_code == 201, comment.text
    comments = client.get(f"/api/v1/tasks/{task_id}/comments", headers=owner_headers)
    assert comments.status_code == 200, comments.text
    assert comments.json()[0]["text"] == "Готово к проверке"

    notifications = client.get("/api/v1/notifications", headers=owner_headers)
    assert notifications.status_code == 200, notifications.text
    kinds = {item["kind"] for item in notifications.json()}
    assert {"task_moved", "task_commented"}.issubset(kinds)

    deleted = client.delete(f"/api/v1/tasks/{task_id}", headers=guest_headers)
    assert deleted.status_code == 204, deleted.text
    assert client.get(f"/api/v1/tasks/{task_id}/comments", headers=owner_headers).status_code == 404
    notifications_after_delete = client.get("/api/v1/notifications", headers=owner_headers)
    assert any(item["kind"] == "task_deleted" for item in notifications_after_delete.json())


def test_favorite_archive_and_search_endpoints(client, created_users):
    owner = register(client, created_users, name="Searchable User")
    teammate = register(client, created_users, name="Searchable Teammate")
    workspace, board = default_workspace_and_board(client, owner["access_token"])
    headers = auth_headers(owner["access_token"])

    assert board["is_favorite"] is True
    favorite_response = client.post(f"/api/v1/workspaces/{workspace['id']}/boards/{board['id']}/favorite", headers=headers)
    assert favorite_response.status_code == 200, favorite_response.text
    favorite_response = client.post(f"/api/v1/workspaces/{workspace['id']}/boards/{board['id']}/favorite", headers=headers)
    assert favorite_response.status_code == 200, favorite_response.text

    archive_response = client.post(f"/api/v1/workspaces/{workspace['id']}/boards/{board['id']}/archive", headers=headers)
    assert archive_response.status_code == 200, archive_response.text

    active_boards = client.get(f"/api/v1/workspaces/{workspace['id']}/boards", headers=headers)
    assert active_boards.status_code == 200, active_boards.text
    assert all(item["id"] != board["id"] for item in active_boards.json())

    archived_boards = client.get(
        f"/api/v1/workspaces/{workspace['id']}/boards?archived=true",
        headers=headers,
    )
    assert archived_boards.status_code == 200, archived_boards.text
    archived_board = next(item for item in archived_boards.json() if item["id"] == board["id"])
    assert archived_board["is_archived"] is True
    assert archived_board["is_favorite"] is True

    search_response = client.get(
        f"/api/v1/users/search?q={teammate['user']['username']}",
        headers=headers,
    )
    assert search_response.status_code == 200, search_response.text
    assert any(item["username"] == teammate["user"]["username"] for item in search_response.json()["users"])
