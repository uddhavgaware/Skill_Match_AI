"""
SkillMatch AI - Pytest Test Suite Configuration & Fixtures
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.ml.parser import ResumeParser
from backend.ml.recommender import InternshipRecommender


@pytest.fixture(scope="session")
def client():
    """FastAPI TestClient fixture."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def parser():
    """Resume parser engine instance."""
    return ResumeParser()


@pytest.fixture(scope="session")
def recommender():
    """Internship recommendation engine instance."""
    return InternshipRecommender()


@pytest.fixture
def sample_resume_text():
    return """
    Alex Chen
    Email: alex.chen@berkeley.edu | Phone: (510) 555-0199
    GitHub: https://github.com/alexchen-ai | LinkedIn: https://linkedin.com/in/alexchen-ai
    
    Education:
    B.S. in Electrical Engineering & Computer Science, UC Berkeley (GPA: 3.92)
    Graduation: May 2027
    
    Skills:
    Python, PyTorch, Transformers, Machine Learning, Deep Learning, Computer Vision,
    Scikit-Learn, Docker, Git, FastAPI, SQL, Linux
    
    Experience:
    Undergraduate Machine Learning Researcher | Berkeley AI Research (BAIR)
    - Researched transformer attention probing mechanisms and multi-modal alignment.
    - Trained diffusion models using PyTorch on distributed cluster with Docker.
    - Published benchmark results comparing constitutional AI safety constraints.
    """


@pytest.fixture
def sample_candidate_skills():
    return [
        "Python",
        "PyTorch",
        "Transformers",
        "Machine Learning",
        "Deep Learning",
        "Computer Vision",
        "Docker",
        "FastAPI",
    ]
