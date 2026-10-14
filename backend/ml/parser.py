"""
SkillMatch AI - Resume & Document Parser
Extracts candidate metadata, contact details, education, work experience,
and performs token-based skill extraction and ontology mapping.
"""

import io
import re
from typing import Any, Dict, List, Optional, Set, Tuple

# PyMuPDF
try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

# Fallback pypdf
try:
    import pypdf
except ImportError:
    pypdf = None

# python-docx
try:
    import docx
except ImportError:
    docx = None

from backend.ml.taxonomy import (
    CANONICAL_LOOKUP,
    TAXONOMY,
    compute_skill_pillars,
    get_skill_category,
    normalize_skill,
)


class ResumeParser:
    """Intelligent multi-format resume parser and skill extraction engine."""

    def __init__(self):
        # Precompile regex for multi-word and single-word skills
        self._prepare_skill_patterns()

    def _prepare_skill_patterns(self):
        """Prepares case-insensitive regex patterns for multi-word and single-word skills."""
        # Sort skills by descending token length to ensure 'Machine Learning' matches before 'Learning'
        all_skills = sorted(list(CANONICAL_LOOKUP.keys()), key=lambda s: len(s), reverse=True)
        
        self.multi_word_skills = [s for s in all_skills if " " in s or "-" in s or "." in s or "+" in s or "#" in s]
        self.single_word_skills = [s for s in all_skills if s not in self.multi_word_skills]

    @staticmethod
    def extract_text_from_pdf(file_bytes: bytes) -> str:
        """Extracts text from PDF bytes using PyMuPDF or PyPDF."""
        extracted_text = ""
        if fitz is not None:
            try:
                doc = fitz.open(stream=file_bytes, filetype="pdf")
                pages = [page.get_text("text") for page in doc]
                extracted_text = "\n".join(pages)
                if extracted_text.strip():
                    return extracted_text
            except Exception:
                pass

        if pypdf is not None:
            try:
                reader = pypdf.PdfReader(io.BytesIO(file_bytes))
                pages = [page.extract_text() or "" for page in reader.pages]
                extracted_text = "\n".join(pages)
            except Exception:
                pass

        return extracted_text

    @staticmethod
    def extract_text_from_docx(file_bytes: bytes) -> str:
        """Extracts text from DOCX bytes using python-docx."""
        if docx is None:
            return ""
        try:
            doc = docx.Document(io.BytesIO(file_bytes))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            paragraphs.append(cell.text)
            return "\n".join(paragraphs)
        except Exception:
            return ""

    def parse_document(self, content_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Parses document bytes according to file extension."""
        fname_lower = filename.lower()
        if fname_lower.endswith(".pdf"):
            raw_text = self.extract_text_from_pdf(content_bytes)
        elif fname_lower.endswith(".docx") or fname_lower.endswith(".doc"):
            raw_text = self.extract_text_from_docx(content_bytes)
        else:
            # Treat as UTF-8 plain text
            try:
                raw_text = content_bytes.decode("utf-8")
            except UnicodeDecodeError:
                raw_text = content_bytes.decode("latin-1", errors="ignore")

        return self.parse_text(raw_text)

    def parse_text(self, text: str) -> Dict[str, Any]:
        """Main pipeline to parse resume text into structured candidate profile."""
        if not text or not text.strip():
            return {
                "name": "Applicant",
                "email": "",
                "phone": "",
                "links": {},
                "education": "Not specified",
                "extracted_skills": [],
                "skills_by_category": {},
                "radar_pillars": compute_skill_pillars([]),
                "experience_summary": "",
                "raw_text_length": 0
            }

        # 1. Contact Information
        email = self._extract_email(text)
        phone = self._extract_phone(text)
        links = self._extract_links(text)
        name = self._extract_name(text)

        # 2. Education extraction
        education = self._extract_education(text)

        # 3. Skill extraction & normalization
        extracted_skills = self._extract_skills(text)

        # 4. Group skills by taxonomy category
        skills_by_category: Dict[str, List[str]] = {}
        for s in extracted_skills:
            cat = get_skill_category(s)
            skills_by_category.setdefault(cat, []).append(s)

        # 5. Radar competency pillar scores
        radar_pillars = compute_skill_pillars(extracted_skills)

        # 6. Experience snippets / summary
        experience_summary = self._extract_experience_summary(text)

        return {
            "name": name,
            "email": email,
            "phone": phone,
            "links": links,
            "education": education,
            "extracted_skills": extracted_skills,
            "skills_by_category": skills_by_category,
            "radar_pillars": radar_pillars,
            "experience_summary": experience_summary,
            "raw_text_length": len(text)
        }

    def _extract_email(self, text: str) -> str:
        match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
        return match.group(0) if match else ""

    def _extract_phone(self, text: str) -> str:
        # Matches patterns like +1 (555) 123-4567, +91 9876543210, 555-123-4567
        match = re.search(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text)
        return match.group(0).strip() if match else ""

    def _extract_links(self, text: str) -> Dict[str, str]:
        links = {}
        github_match = re.search(r"(?:https?://)?(?:www\.)?github\.com/[A-Za-z0-9_-]+", text, re.IGNORECASE)
        if github_match:
            links["github"] = github_match.group(0)

        linkedin_match = re.search(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[A-Za-z0-9_-]+", text, re.IGNORECASE)
        if linkedin_match:
            links["linkedin"] = linkedin_match.group(0)

        portfolio_match = re.search(r"https?://(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?:/[^\s]*)?", text)
        if portfolio_match and portfolio_match.group(0) not in [links.get("github"), links.get("linkedin")]:
            links["portfolio"] = portfolio_match.group(0)

        return links

    def _extract_name(self, text: str) -> str:
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        for line in lines[:5]:
            # Skip lines with emails, links, or section headings
            if "@" in line or "http" in line or len(line) > 40:
                continue
            if any(h in line.lower() for h in ["resume", "curriculum", "vitae", "contact", "email", "phone", "summary"]):
                continue
            # If line is 2 to 4 capitalized words, it's likely a name
            words = line.split()
            if 2 <= len(words) <= 4 and all(re.match(r"^[A-Z][a-zA-Z\.\'-]+$", w) for w in words):
                return line
        return "Student Candidate"

    def _extract_education(self, text: str) -> str:
        edu_keywords = [
            "Bachelor", "B.S.", "B.Tech", "B.E.", "Master", "M.S.", "M.Tech", "Ph.D",
            "Computer Science", "Software Engineering", "Data Science", "Information Technology",
            "Electrical Engineering", "Artificial Intelligence"
        ]
        lines = text.split("\n")
        edu_lines = []
        for line in lines:
            if any(k.lower() in line.lower() for k in edu_keywords):
                cleaned = line.strip()
                if len(cleaned) < 100 and cleaned not in edu_lines:
                    edu_lines.append(cleaned)
                    if len(edu_lines) >= 2:
                        break

        # Check for GPA
        gpa_match = re.search(r"(?:GPA|CGPA)[:\s]+([0-9]\.[0-9]+(?:\s*/\s*[0-9]+(?:\.0)?)?)", text, re.IGNORECASE)
        gpa_str = f" (GPA: {gpa_match.group(1)})" if gpa_match else ""

        if edu_lines:
            return " | ".join(edu_lines) + gpa_str
        return "B.S. in Computer Science (In Progress)" + gpa_str

    def _extract_skills(self, text: str) -> List[str]:
        found_skills: Set[str] = set()
        text_lower = text.lower()

        # Step 1: Match multi-word skills (like "machine learning", "natural language processing")
        for skill_key in self.multi_word_skills:
            # Escape regex special characters in skill (e.g. C++, C#)
            pattern = r"(?<!\w)" + re.escape(skill_key) + r"(?!\w)"
            if re.search(pattern, text_lower):
                found_skills.add(normalize_skill(skill_key))

        # Step 2: Match single-word skills (like "python", "react", "docker", "aws")
        for skill_key in self.single_word_skills:
            pattern = r"(?<![A-Za-z0-9])" + re.escape(skill_key) + r"(?![A-Za-z0-9])"
            if re.search(pattern, text_lower):
                found_skills.add(normalize_skill(skill_key))

        # Sort alphabetically for stable presentation
        return sorted(list(found_skills))

    def _extract_experience_summary(self, text: str) -> str:
        # Check for year ranges or project bullets
        years = re.findall(r"\b(20[12][0-9]\s*[-–]\s*(?:20[12][0-9]|Present|Current))\b", text, re.IGNORECASE)
        project_count = len(re.findall(r"(?:project|built|developed|implemented|designed|created)\b", text, re.IGNORECASE))
        
        summary_parts = []
        if years:
            summary_parts.append(f"Active timeline across {len(set(years))} recorded periods")
        if project_count > 0:
            summary_parts.append(f"Mentions ~{min(project_count, 12)} development & engineering milestones")
        
        return " • ".join(summary_parts) if summary_parts else "Student projects and coursework experience recorded"
