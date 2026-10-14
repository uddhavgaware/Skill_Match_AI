"""
SkillMatch AI - Production Health Check Tests
Verifies system health endpoints, version metadata, telemetry, and engine statuses.
"""


def test_health_check_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "SkillMatch AI"
    assert data["version"] == "2.0.0"
    assert "uptime_seconds" in data
    assert "timestamp" in data
    assert "ml_engines" in data
    assert data["ml_engines"]["parser"] == "active"
    assert data["ml_engines"]["recommender"] == "active"
    assert data["ml_engines"]["indexed_internships_count"] > 0
    assert "system" in data


def test_api_health_alias(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
