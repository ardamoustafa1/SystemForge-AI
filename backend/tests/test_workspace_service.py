import pytest
from app.models.user import User
from app.services.workspace_service import create_workspace, get_workspace_details, delete_workspace, update_workspace, list_workspaces_for_user
from tests.conftest import TestingSessionLocal

@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def test_user(db_session):
    u = User(email="ws_test@example.com", full_name="Ws Test", password_hash="hash")
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u

def test_create_workspace(db_session, test_user):
    res = create_workspace(db_session, test_user, "Test WS")
    assert res["workspace"].name == "Test WS"
    assert res["role"] == "admin"
    assert test_user.default_workspace_id == res["workspace"].id

def test_list_and_get_workspace(db_session, test_user):
    res = create_workspace(db_session, test_user, "Test WS 2")
    ws_id = res["workspace"].id
    
    lst = list_workspaces_for_user(db_session, test_user)
    assert len(lst) >= 1
    
    details = get_workspace_details(db_session, test_user, ws_id)
    assert details["workspace"].name == "Test WS 2"
    assert details["role"] == "admin"

def test_update_and_delete_workspace(db_session, test_user):
    res = create_workspace(db_session, test_user, "Test WS 3")
    ws_id = res["workspace"].id
    
    update_workspace(db_session, test_user, ws_id, "Updated WS")
    details = get_workspace_details(db_session, test_user, ws_id)
    assert details["workspace"].name == "Updated WS"
    
    delete_workspace(db_session, test_user, ws_id)
    lst = list_workspaces_for_user(db_session, test_user)
    assert not any(w["id"] == ws_id for w in lst)
