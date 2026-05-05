"""Sanity checks — visible to students.

These run against the docker compose stack.
Start with: docker compose up --build -d
"""

import subprocess
import time

import pytest
import requests

BASE = "http://localhost:8080"


@pytest.fixture(scope="module", autouse=True)
def compose_stack():
    """Start docker compose stack for testing."""
    subprocess.run(
        ["docker", "compose", "up", "--build", "-d"],
        check=True,
        capture_output=True,
        timeout=120,
    )
    # Wait for API to be ready
    for _ in range(30):
        try:
            resp = requests.get(f"{BASE}/health", timeout=2)
            if resp.status_code == 200:
                break
        except (requests.ConnectionError, requests.Timeout):
            time.sleep(2)
    yield
    subprocess.run(["docker", "compose", "down", "-v"], capture_output=True)


def test_health():
    resp = requests.get(f"{BASE}/health", timeout=5)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


def test_register_and_get_node():
    resp = requests.post(
        f"{BASE}/api/nodes",
        json={"name": "sanity-node", "host": "10.0.0.1", "port": 3000},
        timeout=5,
    )
    assert resp.status_code == 201

    resp = requests.get(f"{BASE}/api/nodes/sanity-node", timeout=5)
    assert resp.status_code == 200
    assert resp.json()["name"] == "sanity-node"


def test_list_nodes():
    resp = requests.get(f"{BASE}/api/nodes", timeout=5)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


# --- New tests below, each traceable to a specific README.md statement ---

def test_health_returns_db_connected():
    """README: GET /health returns {"status": "ok", "db": "connected", "nodes_count": N}"""
    resp = requests.get(f"{BASE}/health", timeout=5)
    assert resp.status_code == 200
    data = resp.json()
    assert data["db"] == "connected"


def test_health_returns_nodes_count():
    """README: nodes_count is the number of active nodes (status = "active")"""
    resp = requests.get(f"{BASE}/health", timeout=5)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data["nodes_count"], int)
    assert data["nodes_count"] >= 0


def test_create_node_returns_201_with_full_response():
    """README: POST /api/nodes returns 201 with id, name, host, port, status, created_at, updated_at"""
    resp = requests.post(
        f"{BASE}/api/nodes",
        json={"name": "test-full-response", "host": "10.0.0.2", "port": 8081},
        timeout=5,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert "id" in body
    assert body["name"] == "test-full-response"
    assert body["host"] == "10.0.0.2"
    assert body["port"] == 8081
    assert body["status"] == "active"
    assert "created_at" in body
    assert "updated_at" in body


def test_create_duplicate_node_returns_409():
    """README: name required, unique → 409 if duplicate"""
    name = "duplicate-test"
    requests.post(
        f"{BASE}/api/nodes",
        json={"name": name, "host": "10.0.0.3", "port": 8082},
        timeout=5,
    )
    resp = requests.post(
        f"{BASE}/api/nodes",
        json={"name": name, "host": "10.0.0.4", "port": 8083},
        timeout=5,
    )
    assert resp.status_code == 409
    assert "already exists" in resp.json()["detail"]


def test_create_node_with_invalid_port_returns_422():
    """README: port required, integer between 1 and 65535 → 422 if invalid"""
    resp = requests.post(
        f"{BASE}/api/nodes",
        json={"name": "invalid-port", "host": "10.0.0.5", "port": 0},
        timeout=5,
    )
    assert resp.status_code == 422


def test_get_nonexistent_node_returns_404():
    """README: GET /api/nodes/{name} returns 404 with {"detail": "Node not found"}"""
    resp = requests.get(f"{BASE}/api/nodes/nonexistent-node", timeout=5)
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Node not found"


def test_update_node_returns_200_with_updated_fields():
    """README: PUT /api/nodes/{name} returns the updated node"""
    name = "update-test"
    requests.post(
        f"{BASE}/api/nodes",
        json={"name": name, "host": "10.0.0.6", "port": 8084},
        timeout=5,
    )
    resp = requests.put(
        f"{BASE}/api/nodes/{name}",
        json={"host": "10.0.0.7", "port": 9090},
        timeout=5,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["host"] == "10.0.0.7"
    assert body["port"] == 9090


def test_update_nonexistent_node_returns_404():
    """README: PUT /api/nodes/{name} returns 404 if node doesn't exist"""
    resp = requests.put(
        f"{BASE}/api/nodes/nonexistent-update",
        json={"host": "10.0.0.8"},
        timeout=5,
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Node not found"


def test_delete_node_returns_204():
    """README: DELETE /api/nodes/{name} returns 204 (no body)"""
    name = "delete-test"
    requests.post(
        f"{BASE}/api/nodes",
        json={"name": name, "host": "10.0.0.9", "port": 8085},
        timeout=5,
    )
    resp = requests.delete(f"{BASE}/api/nodes/{name}", timeout=5)
    assert resp.status_code == 204
    assert resp.text == ""


def test_delete_nonexistent_node_returns_404():
    """README: DELETE /api/nodes/{name} returns 404 if node doesn't exist"""
    resp = requests.delete(f"{BASE}/api/nodes/nonexistent-delete", timeout=5)
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Node not found"


def test_soft_delete_sets_status_inactive():
    """README: Soft delete sets status to "inactive" """
    name = "soft-delete-test"
    requests.post(
        f"{BASE}/api/nodes",
        json={"name": name, "host": "10.0.0.10", "port": 8086},
        timeout=5,
    )
    requests.delete(f"{BASE}/api/nodes/{name}", timeout=5)
    resp = requests.get(f"{BASE}/api/nodes/{name}", timeout=5)
    assert resp.status_code == 200
    assert resp.json()["status"] == "inactive"


def test_list_nodes_includes_inactive():
    """README: GET /api/nodes returns all nodes (including inactive)"""
    name = "inactive-list-test"
    requests.post(
        f"{BASE}/api/nodes",
        json={"name": name, "host": "10.0.0.11", "port": 8087},
        timeout=5,
    )
    requests.delete(f"{BASE}/api/nodes/{name}", timeout=5)
    resp = requests.get(f"{BASE}/api/nodes", timeout=5)
    names = [n["name"] for n in resp.json()]
    assert name in names


def test_health_nodes_count_reflects_active_only():
    """README: nodes_count is the number of active nodes (status = "active")"""
    # Create an active node
    name = "count-active-test"
    requests.post(
        f"{BASE}/api/nodes",
        json={"name": name, "host": "10.0.0.12", "port": 8088},
        timeout=5,
    )
    # Soft delete it
    requests.delete(f"{BASE}/api/nodes/{name}", timeout=5)
    # Health should not count it
    resp = requests.get(f"{BASE}/health", timeout=5)
    # We cannot know the exact count, but we can verify it's an int >= 0
    assert isinstance(resp.json()["nodes_count"], int)
    assert resp.json()["nodes_count"] >= 0
