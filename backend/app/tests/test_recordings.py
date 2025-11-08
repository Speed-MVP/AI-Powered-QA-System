import pytest
from fastapi import status


def test_get_signed_url(client, sample_token, test_user):
    """Test get signed upload URL"""
    response = client.post(
        "/api/recordings/signed-url",
        params={"file_name": "test.mp3"},
        headers={"Authorization": f"Bearer {sample_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "signed_url" in data
    assert "file_url" in data
    assert "file_name" in data


def test_upload_recording(client, sample_token, test_user):
    """Test upload recording"""
    response = client.post(
        "/api/recordings/upload",
        json={
            "file_name": "test.mp3",
            "file_url": "https://storage.googleapis.com/bucket/test.mp3"
        },
        headers={"Authorization": f"Bearer {sample_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "id" in data
    assert data["file_name"] == "test.mp3"
    assert data["status"] == "queued"


def test_list_recordings(client, sample_token, test_user):
    """Test list recordings"""
    # First create a recording
    client.post(
        "/api/recordings/upload",
        json={
            "file_name": "test.mp3",
            "file_url": "https://storage.googleapis.com/bucket/test.mp3"
        },
        headers={"Authorization": f"Bearer {sample_token}"}
    )
    
    # Then list recordings
    response = client.get(
        "/api/recordings/list",
        headers={"Authorization": f"Bearer {sample_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_get_recording(client, sample_token, test_user):
    """Test get specific recording"""
    # First create a recording
    create_response = client.post(
        "/api/recordings/upload",
        json={
            "file_name": "test.mp3",
            "file_url": "https://storage.googleapis.com/bucket/test.mp3"
        },
        headers={"Authorization": f"Bearer {sample_token}"}
    )
    
    recording_id = create_response.json()["id"]
    
    # Then get the recording
    response = client.get(
        f"/api/recordings/{recording_id}",
        headers={"Authorization": f"Bearer {sample_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == recording_id
    assert data["file_name"] == "test.mp3"


def test_get_recording_not_found(client, sample_token):
    """Test get recording that doesn't exist"""
    response = client.get(
        "/api/recordings/invalid-id",
        headers={"Authorization": f"Bearer {sample_token}"}
    )
    
    assert response.status_code == status.HTTP_404_NOT_FOUND

