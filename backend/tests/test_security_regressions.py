import pytest
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect

from tests.test_api_flows import auth_headers, default_workspace_and_board, register
from app.realtime.broker import publish_board_event


def ws_ticket(client: TestClient, token: str) -> str:
    response = client.post("/api/v1/auth/ws-ticket", headers=auth_headers(token))
    assert response.status_code == 200, response.text
    return response.json()["ticket"]


def test_shared_member_cannot_mutate_board_metadata(client: TestClient, created_users):
    owner = register(client, created_users, name="Metadata Owner")
    guest = register(client, created_users, name="Metadata Guest")
    workspace, board = default_workspace_and_board(client, owner["access_token"])
    invitation = client.post(f"/api/v1/boards/{board['id']}/invitations", headers=auth_headers(owner["access_token"]), json={}).json()
    assert client.post("/api/v1/invitations/claim", headers=auth_headers(guest["access_token"]), json={"code": invitation["code"]}).status_code == 200
    response = client.patch(f"/api/v1/workspaces/{workspace['id']}/boards/{board['id']}", headers=auth_headers(guest["access_token"]), json={"title": "Чужое изменение"})
    assert response.status_code in {403, 404}


def test_unknown_assignee_is_rejected(client: TestClient, created_users):
    owner = register(client, created_users, name="Assignee Owner")
    workspace, board = default_workspace_and_board(client, owner["access_token"])
    detail = client.get(f"/api/v1/workspaces/{workspace['id']}/boards/{board['id']}", headers=auth_headers(owner["access_token"])).json()
    response = client.post("/api/v1/tasks", headers=auth_headers(owner["access_token"]), json={"column_id": detail["columns"][0]["id"], "title": "Без исполнителя", "assignee_id": 999999})
    assert response.status_code == 400


def test_task_cannot_move_between_boards(client: TestClient, created_users):
    owner = register(client, created_users, name="Move Owner")
    workspace, first = default_workspace_and_board(client, owner["access_token"])
    second = client.post(f"/api/v1/workspaces/{workspace['id']}/boards", headers=auth_headers(owner["access_token"]), json={"title": "Вторая доска", "description": "", "color": "#2563eb"}).json()
    first_detail = client.get(f"/api/v1/workspaces/{workspace['id']}/boards/{first['id']}", headers=auth_headers(owner["access_token"])).json()
    second_detail = client.get(f"/api/v1/workspaces/{workspace['id']}/boards/{second['id']}", headers=auth_headers(owner["access_token"])).json()
    task = client.post("/api/v1/tasks", headers=auth_headers(owner["access_token"]), json={"column_id": first_detail["columns"][0]["id"], "title": "Проверка границ"}).json()
    moved = client.patch(f"/api/v1/tasks/{task['id']}", headers=auth_headers(owner["access_token"]), json={"column_id": second_detail["columns"][0]["id"]})
    assert moved.status_code == 400


def test_websocket_rejects_user_without_board_access(client: TestClient, created_users):
    owner = register(client, created_users, name="Socket Owner")
    guest = register(client, created_users, name="Socket Guest")
    _, board = default_workspace_and_board(client, owner["access_token"])
    with pytest.raises(WebSocketDisconnect) as error:
        with client.websocket_connect(f"/ws/boards/{board['id']}?ticket={ws_ticket(client, guest['access_token'])}"):
            pass
    assert error.value.code == 1008


def test_websocket_ticket_is_single_use(client: TestClient, created_users):
    owner = register(client, created_users, name="Ticket Owner")
    _, board = default_workspace_and_board(client, owner["access_token"])
    ticket = ws_ticket(client, owner["access_token"])
    with client.websocket_connect(f"/ws/boards/{board['id']}?ticket={ticket}"):
        pass
    with pytest.raises(WebSocketDisconnect) as error:
        with client.websocket_connect(f"/ws/boards/{board['id']}?ticket={ticket}"):
            pass
    assert error.value.code == 1008


def test_websocket_delivers_redis_event_to_connected_members(client: TestClient, created_users):
    owner = register(client, created_users, name="Realtime Owner")
    guest = register(client, created_users, name="Realtime Guest")
    _, board = default_workspace_and_board(client, owner["access_token"])
    invitation = client.post(f"/api/v1/boards/{board['id']}/invitations", headers=auth_headers(owner["access_token"]), json={}).json()
    assert client.post("/api/v1/invitations/claim", headers=auth_headers(guest["access_token"]), json={"code": invitation["code"]}).status_code == 200
    event = {"type": "task.updated", "board_id": board["id"], "task_id": 42}
    with client.websocket_connect(f"/ws/boards/{board['id']}?ticket={ws_ticket(client, owner['access_token'])}") as owner_socket:
        with client.websocket_connect(f"/ws/boards/{board['id']}?ticket={ws_ticket(client, guest['access_token'])}") as guest_socket:
            publish_board_event(board["id"], event)
            assert owner_socket.receive_json() == event
            assert guest_socket.receive_json() == event


def test_demo_endpoint_is_explicit(client: TestClient, created_users):
    response = client.post("/api/v1/auth/demo")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["user"]["name"] == "Alex Morgan"
    assert payload["user"]["username"].startswith("alex-demo-")
    created_users.append(payload["user"]["id"])
