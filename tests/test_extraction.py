from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app.main import app
from app.schemas.extraction import ExtractionResponse

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@patch("app.api.endpoints.ExtractionService")
def test_extract_endpoint(mock_service_cls):
    # Mock the service instance and its extract method
    mock_service = mock_service_cls.return_value
    mock_response = ExtractionResponse(
        markdown="# Test Document",
        tables=[],
        metadata={"filename": "test.pdf", "page_count": 1}
    )
    mock_service.extract = AsyncMock(return_value=mock_response)

    # Create a dummy file
    files = {"file": ("test.pdf", b"dummy content", "application/pdf")}
    
    # We need to override the dependency to return our mock
    # However, since we patched the class where it's imported in endpoints, 
    # the default dependency (which instantiates the class) should use the mock.
    # Let's verify if we need to override_dependency.
    # Actually, simpler to patch the dependency directly if possible, or just the method.
    
    with patch("app.api.endpoints.get_extraction_service", return_value=mock_service):
        response = client.post("/api/v1/extract", files=files)
        
    assert response.status_code == 200
    data = response.json()
    assert data["markdown"] == "# Test Document"
    assert data["metadata"]["filename"] == "test.pdf"
