import pytest
from backend.database import Database
from bson import ObjectId

@pytest.fixture
def db():
    return Database()

def test_db_connection(db):
    try:
        db.client.admin.command('ping')
        connected = True
    except Exception:
        connected = False
    assert connected is True

def test_insert_and_delete_history(db):
    test_data = {
        "text": "Test original text",
        "model": "test-model",
        "chunk_size_1": 100,
        "chunk_overlap_1": 0,
        "chunk_size_2": 100,
        "chunk_overlap_2": 0,
        "token_max": 4000,
        "use_map": False,
        "summary": "Test summary text",
        "processing_time": 1.23
    }
    result = db.insert_history(test_data)
    assert result.inserted_id is not None
    inserted_id = str(result.inserted_id)

    history = db.get_history()
    assert isinstance(history, list)
    found = any(item['id'] == inserted_id for item in history)
    assert found is True

    delete_result = db.delete_history(inserted_id)
    assert delete_result.deleted_count == 1

    history_after_delete = db.get_history()
    found_after = any(item['id'] == inserted_id for item in history_after_delete)
    assert found_after is False
