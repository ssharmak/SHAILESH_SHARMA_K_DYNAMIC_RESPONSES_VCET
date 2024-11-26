import unittest
from unittest.mock import patch
from src.asana_api import get_tasks

@patch("src.asana_api.requests.get")
def test_get_tasks(mock_get):
    mock_get.return_value.json.return_value = {"data": [{"id": "123", "name": "Test Task"}]}
    tasks = get_tasks()
    assert tasks[0]["id"] == "123"
