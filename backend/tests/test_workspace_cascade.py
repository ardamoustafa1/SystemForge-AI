import pytest
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember, RoleEnum
from app.models.design import Design
from tests.conftest import TestingSessionLocal
from app.core.security import hash_password

def test_workspace_cascade_delete():
    db = TestingSessionLocal()
    
    # Create user
    user = User(email="cascade@example.com", full_name="Cascade User", password_hash=hash_password("test"))
    db.add(user)
    db.commit()
    
    # Create workspace
    workspace = Workspace(name="Cascade Workspace")
    db.add(workspace)
    db.commit()
    
    # Create member
    member = WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role=RoleEnum.admin)
    db.add(member)
    
    # Create design - let's check correct arguments
    design = Design(workspace_id=workspace.id, title="Cascade Design", project_type="web")
    db.add(design)
    db.commit()
    
    ws_id = workspace.id
    user_id = user.id
    design_id = design.id
    
    db.delete(workspace)
    db.commit()
    
    assert db.get(Workspace, ws_id) is None
    assert db.get(WorkspaceMember, member.id) is None
    assert db.get(Design, design_id) is None
    assert db.get(User, user_id) is not None
    
    db.close()
