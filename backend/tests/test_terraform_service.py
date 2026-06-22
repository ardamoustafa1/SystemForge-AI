import io
import zipfile
from app.services.terraform_service import build_terraform_zip
from app.schemas.design import DesignInputPayload, DesignOutputPayload

def test_build_terraform_zip():
    title = "My Test Project"
    design_input = DesignInputPayload(project_title="Test", project_type="web", problem_statement="This is a long enough problem statement for the test to pass.", expected_users="10k", traffic_assumptions="test", budget_sensitivity="high", preferred_stack="fastapi postgres redis", constraints="test", deployment_scope="global", data_sensitivity="low", real_time_required=False, mode="product")
    design_output = DesignOutputPayload.model_construct(core_components=["backend", "frontend", "db"], recommended_implementation_phases=[])
    
    zip_bytes = build_terraform_zip(title, design_input, design_output)
    
    zf = zipfile.ZipFile(io.BytesIO(zip_bytes), "r")
    files = zf.namelist()
    
    assert any("main.tf" in f for f in files)
    assert any("variables.tf" in f for f in files)
    assert any("outputs.tf" in f for f in files)
    
    main_tf = next(f for f in files if f.endswith("main.tf"))
    main_content = zf.read(main_tf).decode("utf-8")
    
    # Verify core infrastructure components are generated based on detected flags
    assert "module \"vpc\"" in main_content
    assert "aws_ecs_cluster" in main_content
    assert "module \"db\"" in main_content
    assert "aws_elasticache_cluster" in main_content
    assert "aws_docdb_cluster" not in main_content

def test_build_terraform_zip_mongo():
    title = "Mongo Project"
    design_input = DesignInputPayload(project_title="Test", project_type="web", problem_statement="This is a long enough problem statement for the test to pass.", expected_users="10k", traffic_assumptions="test", budget_sensitivity="high", preferred_stack="nestjs mongo", constraints="test", deployment_scope="global", data_sensitivity="low", real_time_required=False, mode="product")
    design_output = DesignOutputPayload.model_construct(core_components=["backend", "frontend", "db"], recommended_implementation_phases=[])
    
    zip_bytes = build_terraform_zip(title, design_input, design_output)
    
    zf = zipfile.ZipFile(io.BytesIO(zip_bytes), "r")
    files = zf.namelist()
    
    main_tf = next(f for f in files if f.endswith("main.tf"))
    main_content = zf.read(main_tf).decode("utf-8")
    assert "aws_docdb_cluster" in main_content
