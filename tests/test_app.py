from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    original_activities = deepcopy(activities)
    with TestClient(app) as test_client:
        yield test_client
    activities.clear()
    activities.update(original_activities)


def test_root_redirects_to_frontend(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_data(client):
    response = client.get("/activities")

    assert response.status_code == 200
    assert "Chess Club" in response.json()
    assert response.json()["Chess Club"]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]


def test_signup_rejects_duplicate_participant(client):
    email = "new.student@mergington.edu"

    signup_response = client.post(
        "/activities/Chess Club/signup", params={"email": email}
    )
    duplicate_response = client.post(
        "/activities/Chess Club/signup", params={"email": email}
    )

    assert signup_response.status_code == 200
    assert duplicate_response.status_code == 400
    assert duplicate_response.json()["detail"] == (
        "Student is already signed up for this activity"
    )


def test_signup_returns_not_found_for_unknown_activity(client):
    response = client.post(
        "/activities/Unknown Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant(client):
    email = "student@mergington.edu"
    client.post("/activities/Soccer Team/signup", params={"email": email})

    response = client.delete(f"/activities/Soccer Team/participants/{email}")

    assert response.status_code == 200
    assert response.json()["message"] == "Unregistered student@mergington.edu from Soccer Team"
    assert email not in client.get("/activities").json()["Soccer Team"]["participants"]


def test_unregister_returns_not_found_for_missing_participant(client):
    response = client.delete(
        "/activities/Soccer Team/participants/missing@mergington.edu"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
