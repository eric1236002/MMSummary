import pytest
from unittest.mock import MagicMock
import sys
from types import ModuleType

@pytest.fixture(autouse=True)
def mock_db(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake-key-for-testing")
    monkeypatch.setenv("MONGODB_URL", "mongodb://localhost:27017")
    
    # Create a mock database instance
    mock_db_instance = MagicMock()
    mock_db_instance.insert_history.return_value = MagicMock(inserted_id="fake_id")
    mock_db_instance.get_history.return_value = []
    mock_db_instance.delete_history.return_value = MagicMock(deleted_count=1)
    mock_db_instance.client.admin.command.return_value = {"ok": 1.0}
    
    # Patch the Database class in backend.database
    monkeypatch.setattr("backend.database.Database", lambda: mock_db_instance)
    
    # If the app is already imported and initialized, we might need to patch the instance in api.py
    if "backend.api" in sys.modules:
        monkeypatch.setattr("backend.api.database", mock_db_instance)
    
    return mock_db_instance
