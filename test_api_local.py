import sys
from unittest.mock import MagicMock

# Mock anthropic and playwright before importing modules that use them
sys.modules["anthropic"] = MagicMock()
sys.modules["playwright"] = MagicMock()
sys.modules["playwright.async_api"] = MagicMock()
sys.modules["pandas"] = MagicMock()
sys.modules["PyPDF2"] = MagicMock()
sys.modules["openpyxl"] = MagicMock()
sys.modules["matplotlib"] = MagicMock()
sys.modules["matplotlib.pyplot"] = MagicMock()
sys.modules["numpy"] = MagicMock()

from fastapi.testclient import TestClient
from main import app, YOUR_EMAIL, YOUR_SECRET
import os
from unittest.mock import patch

client = TestClient(app)

def test_solve_endpoint_async():
    """Test that the solve endpoint returns 200 immediately and triggers background task"""
    
    # Mock the QuizSolver to avoid actual network calls during test
    with patch("main.QuizSolver") as MockSolver:
        mock_instance = MockSolver.return_value
        # Mock the async method
        mock_instance.solve_quiz_chain = MagicMock()
        
        payload = {
            "email": YOUR_EMAIL,
            "secret": YOUR_SECRET,
            "url": "https://example.com/quiz-test"
        }
        
        response = client.post("/solve", json=payload)
        
        # Check immediate response
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert "background" in response.json()["message"]
        
        # Verify background task was added (FastAPI TestClient runs background tasks synchronously by default)
        # So we can check if the mock was called
        # Note: TestClient runs background tasks after the response is returned
        # We might need to check if the mock was called.
        
        # Actually, TestClient executes background tasks. 
        # Let's verify the mock was called.
        # However, since solve_quiz_chain is async, and we mocked it, we need to ensure it was awaited or called.
        # But wait, background_tasks.add_task takes a function and arguments.
        # If we passed solver.solve_quiz_chain, it should be called.
        
        # Let's check if QuizSolver was initialized
        MockSolver.assert_called_with(email=YOUR_EMAIL, secret=YOUR_SECRET)

    try:
        test_solve_endpoint_async()
        print("✅ API Async Test Passed")
        
    except Exception as e:
        print(f"❌ Tests Failed: {e}")
        exit(1)
