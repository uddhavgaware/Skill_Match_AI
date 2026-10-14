"""
SkillMatch AI - Resume Parser & Skill Extraction Unit Tests
Verifies parsing of resume text, metadata extraction, skill matching, and normalization.
"""

from backend.ml.taxonomy import CANONICAL_LOOKUP, normalize_skill


def test_resume_parser_metadata_extraction(parser, sample_resume_text):
    profile = parser.parse_text(sample_resume_text)
    assert profile["name"] != ""
    assert "alex" in profile["name"].lower() or "chen" in profile["name"].lower()
    assert profile["email"] == "alex.chen@berkeley.edu"
    assert "510" in profile["phone"] or "555" in profile["phone"]
    assert "github.com/alexchen-ai" in profile["links"].get("github", "")
    assert len(profile["extracted_skills"]) > 5


def test_skill_ontology_normalization():
    # Verify variations resolve to canonical forms
    assert normalize_skill("pytorch") == "PyTorch"
    assert normalize_skill("python3") == "Python"
    assert normalize_skill("reactjs") == "React"
    assert normalize_skill("k8s") == "Kubernetes"
    assert normalize_skill("postgres") == "PostgreSQL"
    assert normalize_skill("docker") == "Docker"


def test_radar_pillars_computation(parser, sample_resume_text):
    profile = parser.parse_text(sample_resume_text)
    radar = profile["radar_pillars"]
    assert isinstance(radar, dict)
    assert "AI & ML" in radar
    assert "Fullstack" in radar
    assert "Cloud & DevOps" in radar
    # With PyTorch, Transformers, Deep Learning, ML, AI & ML score should be high
    assert radar["AI & ML"] > 50.0
