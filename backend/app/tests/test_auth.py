import pytest
from fastapi import status


def test_login_success(client, test_user):
    """Test successful login"""
    response = client.post(
        "/api/auth/login",
        json={
            "email": "test@example.com",
            "password": "testpassword"
        }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user_id"] == test_user.id


def test_login_invalid_email(client):
    """Test login with invalid email"""
    response = client.post(
        "/api/auth/login",
        json={
            "email": "invalid@example.com",
            "password": "testpassword"
        }
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_login_invalid_password(client, test_user):
    """Test login with invalid password"""
    response = client.post(
        "/api/auth/login",
        json={
            "email": "test@example.com",
            "password": "wrongpassword"
        }
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_me(client, sample_token):
    """Test get current user"""
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {sample_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "id" in data
    assert "email" in data
    assert data["email"] == "test@example.com"


def test_get_me_unauthorized(client):
    """Test get current user without token"""
    response = client.get("/api/auth/me")
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

