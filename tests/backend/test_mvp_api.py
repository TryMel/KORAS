import sys

sys.path.insert(0, "backend")

from fastapi.testclient import TestClient
from app.main import app


def test_local_action_requires_device_observation_before_success():
    with TestClient(app) as client:
        planned = client.post("/api/v1/agent/run", json={"user_input": "Ouvre Maps"})
        assert planned.status_code == 200
        body = planned.json()
        assert body["state"] == "READY_TO_EXECUTE"
        assert body["is_terminal"] is False

        step = body["steps"][0]
        completed = client.post(
            f"/api/v1/agent/runs/{body['run_id']}/steps/{step['step_id']}/result",
            json={"status": "verified", "result": {"verified": True, "opened": True}},
        )
        assert completed.status_code == 200
        assert completed.json()["state"] == "SUCCESS"


def test_external_action_requires_confirmation_before_device_execution():
    with TestClient(app) as client:
        planned = client.post("/api/v1/agent/run", json={"user_input": "Appelle maman"})
        body = planned.json()
        assert body["state"] == "WAITING_FOR_CONFIRMATION"
        step = body["steps"][0]

        premature = client.post(
            f"/api/v1/agent/runs/{body['run_id']}/steps/{step['step_id']}/result",
            json={"status": "verified", "result": {"verified": True}},
        )
        assert premature.status_code == 409

        approved = client.post(
            f"/api/v1/agent/runs/{body['run_id']}/confirm",
            json={"step_id": step["step_id"]},
        )
        assert approved.status_code == 200
        assert approved.json()["state"] == "READY_TO_EXECUTE"


def test_multi_action_run_requests_each_confirmation_in_order():
    with TestClient(app) as client:
        planned = client.post(
            "/api/v1/agent/run",
            json={"user_input": "Appelle maman puis crée un événement réunion"},
        )
        assert planned.status_code == 200
        body = planned.json()
        assert body["state"] == "WAITING_FOR_CONFIRMATION"
        first_step, second_step = body["steps"]
        assert body["awaiting_confirmation_step_id"] == first_step["step_id"]

        premature_second_approval = client.post(
            f"/api/v1/agent/runs/{body['run_id']}/confirm",
            json={"step_id": second_step["step_id"]},
        )
        assert premature_second_approval.status_code == 409

        approved_first = client.post(
            f"/api/v1/agent/runs/{body['run_id']}/confirm",
            json={"step_id": first_step["step_id"]},
        )
        assert approved_first.status_code == 200
        assert approved_first.json()["state"] == "READY_TO_EXECUTE"

        completed_first = client.post(
            f"/api/v1/agent/runs/{body['run_id']}/steps/{first_step['step_id']}/result",
            json={"status": "verified", "result": {"verified": True, "launched": True}},
        )
        assert completed_first.status_code == 200
        next_run = completed_first.json()
        assert next_run["state"] == "WAITING_FOR_CONFIRMATION"
        assert next_run["awaiting_confirmation_step_id"] == second_step["step_id"]

        approved_second = client.post(
            f"/api/v1/agent/runs/{body['run_id']}/confirm",
            json={"step_id": second_step["step_id"]},
        )
        assert approved_second.status_code == 200
        assert approved_second.json()["state"] == "READY_TO_EXECUTE"

        completed_second = client.post(
            f"/api/v1/agent/runs/{body['run_id']}/steps/{second_step['step_id']}/result",
            json={"status": "verified", "result": {"verified": True, "launched": True}},
        )
        assert completed_second.status_code == 200
        assert completed_second.json()["state"] == "SUCCESS"
