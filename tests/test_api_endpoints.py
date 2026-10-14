"""
SkillMatch AI - REST API Endpoints Integration Tests
Tests all core user-facing and recommendation API endpoints.
"""


def test_api_parse_text(client, sample_resume_text):
    response = client.post("/api/parse-text", json={"text": sample_resume_text})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "profile" in data
    assert "recommendations" in data
    assert len(data["profile"]["extracted_skills"]) > 0


def test_api_parse_empty_text(client):
    response = client.post("/api/parse-text", json={"text": "   "})
    assert response.status_code == 400


def test_api_recommend_real_mode(client):
    response = client.post(
        "/api/recommend",
        json={
            "skills": ["Python", "PyTorch", "Transformers", "Machine Learning"],
            "domain": "AI & Machine Learning",
            "top_k": 5
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "real"
    assert "recommendations" in data
    assert len(data["recommendations"]) > 0
    assert "radar_pillars" in data


def test_api_recommend_simulation_mode(client):
    response = client.post(
        "/api/recommend",
        json={
            "skills": ["Python"],
            "simulated_skills": ["PyTorch", "Transformers", "Deep Learning"],
            "mode": "simulation",
            "top_k": 5
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "simulation"
    assert len(data["recommendations"]) > 0
    top_rec = data["recommendations"][0]
    assert "score_delta" in top_rec
    assert "simulated_match_score" in top_rec


def test_api_skill_gap(client):
    response = client.post(
        "/api/skill-gap",
        json={
            "skills": ["Python", "SQL"],
            "internship_id": "int-01"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "missing_required" in data
    assert "learning_pathways" in data
    assert "readiness_percentage" in data


def test_api_skill_gap_not_found(client):
    response = client.post(
        "/api/skill-gap",
        json={
            "skills": ["Python"],
            "internship_id": "non-existent-id-12345"
        }
    )
    assert response.status_code == 404


def test_api_simulate_endpoint(client):
    response = client.post(
        "/api/simulate",
        json={
            "current_skills": ["Python"],
            "skills_to_add": ["PyTorch", "Transformers"],
            "internship_id": "int-01"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "current_score" in data
    assert "projected_score" in data
    assert "score_delta" in data


def test_api_list_internships(client):
    response = client.get("/api/internships")
    assert response.status_code == 200
    data = response.json()
    assert "internships" in data
    assert data["count"] > 0


def test_api_internship_detail(client):
    response = client.get("/api/internships/int-01")
    assert response.status_code == 200
    job = response.json()
    assert job["id"] == "int-01"
    assert job["company"] == "Anthropic AI"


def test_api_internship_detail_404(client):
    response = client.get("/api/internships/int-does-not-exist")
    assert response.status_code == 404


def test_api_market_trends(client):
    response = client.get("/api/market-trends")
    assert response.status_code == 200
    data = response.json()
    assert "top_demanded_skills" in data
    assert "domain_distribution" in data
    assert data["total_internships"] > 0


def test_api_taxonomy(client):
    response = client.get("/api/taxonomy")
    assert response.status_code == 200
    data = response.json()
    assert "taxonomy" in data
    assert "all_skills" in data
    assert len(data["all_skills"]) > 50


def test_api_samples(client):
    response = client.get("/api/samples")
    assert response.status_code == 200
    data = response.json()
    assert "samples" in data
    assert len(data["samples"]) > 0


def test_api_simulation_scenarios(client):
    response = client.get("/api/simulation-scenarios")
    assert response.status_code == 200
    data = response.json()
    assert "scenarios" in data
    assert len(data["scenarios"]) >= 3
