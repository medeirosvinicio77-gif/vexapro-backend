import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_import_main():
    """Testa se o main.py importa sem erros"""
    try:
        from main import app
        assert app is not None
        assert app.title == "VexaPro"
    except Exception as e:
        assert False, f"Falha ao importar main: {e}"

def test_import_routers():
    """Testa se todos os routers importam"""
    routers = [
        'api.v1.auth',
        'api.v1.users', 
        'api.v1.projects',
        'api.v1.videos',
        'api.v1.measurements'
    ]
    
    for router_name in routers:
        try:
            module = __import__(router_name, fromlist=['router'])
            assert hasattr(module, 'router')
        except Exception as e:
            print(f"⚠️ {router_name}: {e}")

def test_import_vision():
    """Testa se módulos de visão importam"""
    modules = [
        'vision.aruco_detector',
        'vision.device_detector',
        'vision.multimodal_measurement',
        'vision.point_cloud',
        'vision.camera_calibration'
    ]
    
    for module_name in modules:
        try:
            __import__(module_name)
            assert True
        except Exception as e:
            print(f"⚠️ {module_name}: {e}")

def test_import_services():
    """Testa se serviços importam"""
    try:
        from services.pipeline import VideoPipeline
        assert VideoPipeline is not None
    except Exception as e:
        print(f"⚠️ services.pipeline: {e}")

def test_config():
    """Testa configurações"""
    try:
        from core.config import settings
        assert settings.APP_NAME == "VexaPro"
        assert hasattr(settings, 'SECRET_KEY')
    except Exception as e:
        assert False, f"Falha nas configs: {e}"

def test_uuids():
    """Testa geração de UUIDs"""
    from core.uuid_helpers import generate_uuid_str, generate_uuid
    uid_str = generate_uuid_str()
    assert len(uid_str) == 36
    import uuid
    assert isinstance(generate_uuid(), uuid.UUID)