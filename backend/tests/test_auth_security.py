import pytest
from app.core.security import hash_password, verify_password
from tests.test_api_flows import register_and_login

def test_password_hashing():
    pwd = "securepassword123"
    hashed = hash_password(pwd)
    assert verify_password(pwd, hashed)
    assert not verify_password("wrongpassword", hashed)

def test_token_replay_and_rotation(client):
    headers = register_and_login(client, "replaytest@example.com")
    
    # Login again to get refresh token manually
    login_resp = client.post("/api/auth/login", json={"email": "replaytest@example.com", "password": "StrongPass1"})
    assert login_resp.status_code == 200
    refresh_token = login_resp.cookies.get("sf_refresh_token")
    assert refresh_token
    
    # Rotate token using the refresh endpoint
    rotate_resp = client.post("/api/auth/refresh", cookies={"sf_refresh_token": refresh_token})
    assert rotate_resp.status_code == 200
    new_refresh = rotate_resp.cookies.get("sf_refresh_token")
    
    # Replay original token -> should be rejected because it's rotated/revoked
    replay_resp = client.post("/api/auth/refresh", cookies={"sf_refresh_token": refresh_token})
    assert replay_resp.status_code == 401
    
    # Replay with invalid signature/fake token
    fake_resp = client.post("/api/auth/refresh", cookies={"sf_refresh_token": "fake_token_data_here"})
    assert fake_resp.status_code == 401
