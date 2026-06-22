import io
import zipfile
from app.services.scaffold_service import build_scaffold_zip
from app.schemas.design import DesignInputPayload, DesignOutputPayload

def test_build_scaffold_zip_fastapi_nextjs_postgres():
    title = "My Test Project"
    design_input = DesignInputPayload(project_title="Test", project_type="web", problem_statement="This is a long enough problem statement for the test to pass.", expected_users="10k", traffic_assumptions="test", budget_sensitivity="high", preferred_stack="fastapi nextjs postgres", constraints="test", deployment_scope="global", data_sensitivity="low", real_time_required=False, mode="product")
    design_output = DesignOutputPayload.model_construct(core_components=["backend", "frontend", "db"], recommended_implementation_phases=[])
    
    zip_bytes = build_scaffold_zip(title, design_input, design_output)
    
    zf = zipfile.ZipFile(io.BytesIO(zip_bytes), "r")
    files = zf.namelist()
    
    assert any("docker-compose.yml" in f for f in files)
    assert any("README.md" in f for f in files)
    
    dc_file = next(f for f in files if f.endswith("docker-compose.yml"))
    dc_content = zf.read(dc_file).decode("utf-8")
    assert "backend:" in dc_content
    assert "frontend:" in dc_content
    assert "postgres:" in dc_content
    
    # Assert specific FastAPI and Next.js files
    assert any(f.endswith("backend/requirements.txt") for f in files)
    assert any(f.endswith("frontend/package.json") for f in files)

def test_build_scaffold_zip_django_vite_mongo():
    title = "My Test Project"
    design_input = DesignInputPayload(project_title="Test", project_type="web", problem_statement="This is a long enough problem statement for the test to pass.", expected_users="10k", traffic_assumptions="test", budget_sensitivity="high", preferred_stack="django vite mongo", constraints="test", deployment_scope="global", data_sensitivity="low", real_time_required=False, mode="product")
    design_output = DesignOutputPayload.model_construct(core_components=["backend", "frontend", "db"], recommended_implementation_phases=[])
    
    zip_bytes = build_scaffold_zip(title, design_input, design_output)
    
    zf = zipfile.ZipFile(io.BytesIO(zip_bytes), "r")
    files = zf.namelist()
    
    dc_file = next(f for f in files if f.endswith("docker-compose.yml"))
    dc_content = zf.read(dc_file).decode("utf-8")
    assert "python manage.py runserver" in dc_content
    assert "mongo:" in dc_content
    assert "postgres:" not in dc_content
