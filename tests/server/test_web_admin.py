"""
Tests for the Web Admin UI authentication functionality
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient
import secrets

from server.web_admin import WebAdmin, SESSIONS

@pytest.fixture
def app():
    """Create FastAPI app for testing"""
    app = FastAPI()
    web_admin = WebAdmin(app)
    return app

@pytest.fixture
def client(app):
    """Create test client"""
    return TestClient(app)

@patch("server.web_admin.load_yaml_config")
def test_login_page_get(mock_load_config, client):
    """Test GET request to login page"""
    # Mock config
    mock_load_config.return_value = {"admin": {}}
    
    # Request login page
    response = client.get("/admin/login")
    
    # Verify response
    assert response.status_code == 200
    assert "Login" in response.text
    assert "Username" in response.text
    assert "Password" in response.text
    
@patch("server.web_admin.load_yaml_config")
@patch("server.web_admin.verify_password_hash")
def test_login_success(mock_verify_password, mock_load_config, client):
    """Test successful login"""
    # Mock config with admin credentials
    mock_load_config.return_value = {
        "admin": {
            "username": "admin",
            "password_hash": "hashed_password"
        }
    }
    
    # Mock password verification
    mock_verify_password.return_value = True
    
    # Submit login form
    response = client.post(
        "/admin/login",
        data={"username": "admin", "password": "correct_password"},
        allow_redirects=False
    )
    
    # Verify redirect to dashboard
    assert response.status_code == 303
    assert response.headers["location"] == "/admin/dashboard"
    
    # Verify session cookie is set
    session_cookie = next((c for c in client.cookies if c.name == "lsl_admin_session"), None)
    assert session_cookie is not None
    
    # Verify session was created
    assert len(SESSIONS) == 1
    session = list(SESSIONS.values())[0]
    assert session["username"] == "admin"
    
@patch("server.web_admin.load_yaml_config")
@patch("server.web_admin.verify_password_hash")
def test_login_incorrect_password(mock_verify_password, mock_load_config, client):
    """Test login with incorrect password"""
    # Mock config with admin credentials
    mock_load_config.return_value = {
        "admin": {
            "username": "admin",
            "password_hash": "hashed_password"
        }
    }
    
    # Mock password verification (fails)
    mock_verify_password.return_value = False
    
    # Submit login form with incorrect password
    response = client.post(
        "/admin/login",
        data={"username": "admin", "password": "wrong_password"},
        allow_redirects=False
    )
    
    # Verify redirect back to login page
    assert response.status_code == 303
    assert response.headers["location"] == "/admin/login"
    
    # Verify no session was created
    session_cookie = next((c for c in client.cookies if c.name == "lsl_admin_session"), None)
    assert session_cookie is None or session_cookie.value == ""
    
def test_logout(client):
    """Test logout functionality"""
    # Create a session
    session_id = secrets.token_urlsafe(32)
    SESSIONS[session_id] = {
        "username": "admin",
        "created_at": "2023-01-01T00:00:00",
        "expires_at": "2099-01-01T00:00:00"  # Far future
    }
    
    # Set session cookie
    client.cookies.set("lsl_admin_session", session_id)
    
    # Request logout
    response = client.get("/admin/logout", allow_redirects=False)
    
    # Verify redirect to login page
    assert response.status_code == 303
    assert response.headers["location"] == "/admin/login"
    
    # Verify session was removed
    assert session_id not in SESSIONS
    
    # Verify cookie was unset
    session_cookie = next((c for c in client.cookies if c.name == "lsl_admin_session"), None)
    assert session_cookie is None or session_cookie.value == ""
    
@patch("server.web_admin.load_yaml_config")
def test_dashboard_authenticated(mock_load_config, client):
    """Test accessing dashboard when authenticated"""
    # Mock config
    mock_load_config.return_value = {"admin": {}}
    
    # Create a session
    session_id = secrets.token_urlsafe(32)
    SESSIONS[session_id] = {
        "username": "admin",
        "created_at": "2023-01-01T00:00:00",
        "expires_at": "2099-01-01T00:00:00"  # Far future
    }
    
    # Set session cookie
    client.cookies.set("lsl_admin_session", session_id)
    
    # Request dashboard
    response = client.get("/admin/dashboard")
    
    # Verify successful access
    assert response.status_code == 200
    assert "Dashboard" in response.text
    assert "admin" in response.text  # Username displayed
    
@patch("server.web_admin.load_yaml_config")
def test_dashboard_unauthenticated(mock_load_config, client):
    """Test accessing dashboard when not authenticated"""
    # Mock config
    mock_load_config.return_value = {"admin": {}}
    
    # Request dashboard without session
    response = client.get("/admin/dashboard", allow_redirects=False)
    
    # Verify redirect to login page
    assert response.status_code == 303
    assert response.headers["location"] == "/admin/login"
    
def test_session_validation():
    """Test session validation logic"""
    # Create WebAdmin instance
    app = FastAPI()
    web_admin = WebAdmin(app)
    
    # Create a valid session
    valid_session_id = secrets.token_urlsafe(32)
    SESSIONS[valid_session_id] = {
        "username": "admin",
        "created_at": "2023-01-01T00:00:00",
        "expires_at": "2099-01-01T00:00:00"  # Far future
    }
    
    # Create an expired session
    expired_session_id = secrets.token_urlsafe(32)
    SESSIONS[expired_session_id] = {
        "username": "admin",
        "created_at": "2023-01-01T00:00:00",
        "expires_at": "2001-01-01T00:00:00"  # Past
    }
    
    # Check valid session
    assert web_admin._validate_session(valid_session_id) is True
    
    # Check expired session
    assert web_admin._validate_session(expired_session_id) is False
    
    # Check expired session was removed
    assert expired_session_id not in SESSIONS
    
    # Check non-existent session
    assert web_admin._validate_session("nonexistent") is False
