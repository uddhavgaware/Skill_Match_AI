"""
SkillMatch AI - Skill Gap Analyzer Unit Tests
Verifies missing skill calculation, roadmap generation, and What-If simulation.
"""

from backend.ml.gap_analyzer import SkillGapAnalyzer


def test_gap_analyzer_missing_skills(recommender):
    job = recommender.internships[0]
    candidate_skills = ["Python"]  # Only Python

    analysis = SkillGapAnalyzer.analyze_gap(candidate_skills, job)
    assert "internship_id" in analysis
    assert "missing_required" in analysis
    assert "missing_preferred" in analysis
    assert "learning_pathways" in analysis
    assert "readiness_percentage" in analysis

    # PyTorch and Transformers are required in int-01, so they must be in missing_required
    missing_req = analysis["missing_required"]
    assert any("pytorch" in s.lower() for s in missing_req)


def test_simulate_what_if_boost(recommender):
    job = recommender.internships[0]
    current_skills = ["Python"]
    skills_to_add = ["PyTorch", "Transformers", "Deep Learning"]

    sim = SkillGapAnalyzer.simulate_what_if(
        current_skills=current_skills,
        skills_to_add=skills_to_add,
        internship=job,
        recommender_engine=recommender
    )

    assert "current_score" in sim
    assert "projected_score" in sim
    assert "score_delta" in sim
    # Adding required skills should boost the match score
    assert sim["projected_score"] > sim["current_score"]
    assert sim["score_delta"] > 0
