"""
SkillMatch AI - Recommender Engine Unit Tests
Verifies hybrid ML recommendation scoring (TF-IDF + BM25 + Skill Overlap),
domain/work-type filtering, thresholding, and candidate ranking.
"""


def test_recommender_basic_matching(recommender, sample_candidate_skills):
    recs = recommender.recommend(
        student_skills=sample_candidate_skills,
        experience_summary="Researching deep learning transformers and computer vision",
        top_k=10
    )
    assert len(recs) > 0
    assert len(recs) <= 10

    # Best match should have high match score
    top_match = recs[0]
    assert "internship" in top_match
    assert "match_score" in top_match
    assert top_match["match_score"] > 60.0
    assert "score_breakdown" in top_match
    assert "tier_badge" in top_match


def test_recommender_domain_filter(recommender, sample_candidate_skills):
    target_domain = "AI & Machine Learning"
    recs = recommender.recommend(
        student_skills=sample_candidate_skills,
        target_domain=target_domain,
        top_k=5
    )
    assert len(recs) > 0
    for r in recs:
        assert r["internship"]["domain"] == target_domain


def test_recommender_work_type_filter(recommender, sample_candidate_skills):
    recs = recommender.recommend(
        student_skills=sample_candidate_skills,
        work_type_filter="Remote",
        top_k=5
    )
    assert len(recs) > 0
    for r in recs:
        assert r["internship"]["work_type"] == "Remote"


def test_recommender_min_score_filter(recommender, sample_candidate_skills):
    min_score = 70.0
    recs = recommender.recommend(
        student_skills=sample_candidate_skills,
        min_match_score=min_score,
        top_k=10
    )
    for r in recs:
        assert r["match_score"] >= min_score


def test_recommender_dynamic_indexing(recommender):
    initial_count = len(recommender.internships)
    new_job = {
        "id": "int-test-999",
        "title": "Quantum Algorithm Researcher",
        "company": "Quantum Corp",
        "domain": "Systems & CS",
        "location": "Boston, MA",
        "work_type": "Onsite",
        "duration": "12 Weeks",
        "stipend": "$60/hr",
        "level": "Graduate",
        "company_initials": "QC",
        "company_color": "#8B5CF6",
        "description": "Develop fault-tolerant quantum algorithms and error correction.",
        "required_skills": ["Python", "Quantum Computing", "Linear Algebra"],
        "preferred_skills": ["Qiskit", "C++"],
        "responsibilities": ["Algorithm design"],
        "learning_outcomes": ["Quantum simulation"]
    }
    recommender.add_internship(new_job)
    assert len(recommender.internships) == initial_count + 1

    # Search for this job specifically
    recs = recommender.recommend(
        student_skills=["Quantum Computing", "Python", "Linear Algebra"],
        top_k=5
    )
    job_ids = [r["internship"]["id"] for r in recs]
    assert "int-test-999" in job_ids
