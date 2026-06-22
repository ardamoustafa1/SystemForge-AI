import pytest
from app.core.config import get_settings

def test_enforce_security_baseline(monkeypatch):
    from app.main import _enforce_security_baseline
    settings = get_settings()
    
    # Test valid dev
    monkeypatch.setattr(settings, "app_env", "development")
    monkeypatch.setattr(settings, "jwt_secret", "change-me")
    _enforce_security_baseline() # should pass
    
    # Test invalid prod
    monkeypatch.setattr(settings, "app_env", "production")
    with pytest.raises(RuntimeError, match="Insecure JWT secret"):
        _enforce_security_baseline()
        
    monkeypatch.setattr(settings, "jwt_secret", "a-very-long-and-secure-secret-key-32-chars")
    monkeypatch.setattr(settings, "cookie_secure", False)
    with pytest.raises(RuntimeError, match="cookie_secure must be true"):
        _enforce_security_baseline()
        
    monkeypatch.setattr(settings, "cookie_secure", True)
    _enforce_security_baseline() # should pass
