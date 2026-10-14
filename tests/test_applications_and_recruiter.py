"""
SkillMatch AI - Applications & Recruiter Workflow Tests
Tests internship application submissions, duplicate prevention, status updates,
job posting by recruiters, and candidate pool scouting.
"""


def test_recruiter_post_internship(client):
    payload = {
        "title": "Embedded Robotics Engineering Intern",
        "company": "Boston Dynamics",
        "domain": "Systems & CS",
        "location": "Waltham, MA",
        "work_type": "Onsite",
        "duration": "12 Weeks (Summer 2026)",
        "stipend": "$55/hr",
        "level": "Undergrad / Masters",
        "description": "Develop low-level C++ motor control algorithms and real-time state estimators.",
        "required_skills": ["C++", "ROS", "Linux", "Robotics"],
        "preferred_skills": ["Python", "Git", "Control Theory"],
        "responsibilities": ["Develop sensor drivers"],
        "learning_outcomes": ["Production robotics"]
    }
    response = client.post("/api/internships", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "internship" in data
    assert data["internship"]["company"] == "Boston Dynamics"


def test_student_apply_flow(client):
    app_payload = {
        "internship_id": "int-02",
        "student_id": "test-student-42",
        "student_name": "Taylor Swiftly",
        "student_email": "taylor@swift.edu",
        "student_education": "B.S. in Computer Science",
        "student_skills": ["TypeScript", "React", "Node.js", "PostgreSQL"],
        "match_score": 93.5
    }
    response = client.post("/api/apply", json=app_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "application" in data
    assert data["application"]["status"] == "Under Review"

    # Test duplicate application prevention
    dup_response = client.post("/api/apply", json=app_payload)
    assert dup_response.status_code == 200
    dup_data = dup_response.json()
    assert dup_data["status"] == "already_applied"


def test_get_applications_filter(client):
    response = client.get("/api/applications?internship_id=int-02")
    assert response.status_code == 200
    data = response.json()
    assert "applications" in data
    assert data["count"] >= 1


def test_update_application_status(client):
    # Fetch existing application
    apps_res = client.get("/api/applications")
    apps = apps_res.json()["applications"]
    assert len(apps) > 0
    target_app_id = apps[0]["id"]

    patch_res = client.patch(
        f"/api/applications/{target_app_id}/status",
        json={"status": "Interview Scheduled"}
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["application"]["status"] == "Interview Scheduled"


def test_recruiter_applicant_ranking(client):
    response = client.get("/api/recruiter/internships/int-01/applicants")
    assert response.status_code == 200
    data = response.json()
    assert "internship" in data
    assert "applicants" in data
    assert len(data["applicants"]) > 0
    # First applicant should have match_score
    assert "match_score" in data["applicants"][0]


def test_candidates_pool(client):
    response = client.get("/api/candidates")
    assert response.status_code == 200
    data = response.json()
    assert "candidates" in data
    assert data["count"] > 0
