"""
SkillMatch AI - Hybrid Recommendation Engine
Combines Exact/Normalized Skill Overlap, TF-IDF Cosine Similarity,
and BM25 Information Retrieval scoring to rank internships and quantify fit.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from backend.ml.taxonomy import normalize_skill


class InternshipRecommender:
    """Hybrid recommendation engine for student-to-internship matching."""

    def __init__(self, internships_filepath: Optional[str] = None):
        if internships_filepath is None:
            internships_filepath = str(Path(__file__).parent.parent / "data" / "internships.json")
        self.internships_filepath = internships_filepath
        self.internships: List[Dict[str, Any]] = []
        self._load_and_index_internships()

    def _load_and_index_internships(self):
        """Loads internships from JSON and builds TF-IDF and BM25 indexing models."""
        with open(self.internships_filepath, "r", encoding="utf-8") as f:
            self.internships = json.load(f)
        self._rebuild_index()

    def _rebuild_index(self):
        """Builds or refreshes TF-IDF and BM25 indexing models for all current internships."""
        self.corpus_texts = []
        self.tokenized_corpus = []

        for item in self.internships:
            req_str = " ".join(item.get("required_skills", []))
            pref_str = " ".join(item.get("preferred_skills", []))
            resp_str = " ".join(item.get("responsibilities", []))
            
            # Rich document text representation
            full_text = f"{item.get('title', '')} {item.get('domain', '')} {item.get('company', '')} {req_str} {pref_str} {item.get('description', '')} {resp_str}"
            self.corpus_texts.append(full_text)

            # Tokenized skills and terms for BM25
            tokens = [w.lower() for w in full_text.replace("/", " ").replace("-", " ").split()]
            self.tokenized_corpus.append(tokens)

        # Fit TF-IDF Vectorizer
        self.tfidf_vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words="english",
            max_features=4000
        )
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(self.corpus_texts)

        # Fit BM25 Model
        self.bm25_model = BM25Okapi(self.tokenized_corpus)

    def add_internship(self, internship: Dict[str, Any]):
        """Adds a newly created internship posting and refreshes indexing."""
        self.internships.insert(0, internship)
        self._rebuild_index()

    def rank_candidates(
        self,
        candidates: List[Dict[str, Any]],
        internship: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Ranks candidate profiles against a specific internship using hybrid scoring.
        Used by the Recruiter Portal to view ranked applicants.
        """
        job_req = [normalize_skill(s) for s in internship.get("required_skills", [])]
        job_pref = [normalize_skill(s) for s in internship.get("preferred_skills", [])]

        ranked = []
        for cand in candidates:
            cand_skills = cand.get("extracted_skills", []) or cand.get("skills", [])
            norm_cand_skills = {normalize_skill(s) for s in cand_skills}

            matched_req = [s for s in job_req if s in norm_cand_skills]
            missing_req = [s for s in job_req if s not in norm_cand_skills]
            matched_pref = [s for s in job_pref if s in norm_cand_skills]
            missing_pref = [s for s in job_pref if s not in norm_cand_skills]

            req_ratio = len(matched_req) / len(job_req) if job_req else 1.0
            pref_ratio = len(matched_pref) / len(job_pref) if job_pref else 1.0
            skill_score = (0.80 * req_ratio) + (0.20 * pref_ratio)

            cand_text = " ".join(cand_skills) + " " + cand.get("experience_summary", "") + " " + cand.get("education", "")
            job_text = f"{internship.get('title','')} {internship.get('description','')} {' '.join(internship.get('required_skills',[]))}"
            
            try:
                tfidf_pair = self.tfidf_vectorizer.transform([cand_text, job_text])
                sim = float(cosine_similarity(tfidf_pair[0:1], tfidf_pair[1:2])[0][0])
            except Exception:
                sim = 0.5

            raw_composite = (0.60 * skill_score) + (0.40 * sim)
            calibrated = self._calibrate_score(raw_composite, req_ratio, pref_ratio)
            tier, tier_color, tier_badge = self._get_tier_info(calibrated)

            ranked.append({
                "candidate": cand,
                "match_score": round(calibrated, 1),
                "tier": tier,
                "tier_color": tier_color,
                "tier_badge": tier_badge,
                "matched_required": matched_req,
                "missing_required": missing_req,
                "matched_preferred": matched_pref,
                "missing_preferred": missing_pref,
                "readiness_pct": round(req_ratio * 100, 1),
                "application_status": cand.get("application_status", "Under Review"),
                "applied_at": cand.get("applied_at", "Recently")
            })

        ranked.sort(key=lambda x: x["match_score"], reverse=True)
        return ranked

    def recommend(
        self,
        student_skills: List[str],
        experience_summary: str = "",
        education: str = "",
        target_domain: Optional[str] = None,
        work_type_filter: Optional[str] = None,
        min_match_score: float = 0.0,
        top_k: int = 15
    ) -> List[Dict[str, Any]]:
        """
        Calculates hybrid match scores for all internships given student profile,
        returns top-K ranked recommendations with breakdown.
        """
        normalized_student_skills = {normalize_skill(s) for s in student_skills}

        # 1. Prepare student text representation for TF-IDF & BM25
        skills_text = " ".join(student_skills)
        student_doc = f"{skills_text} {experience_summary} {education}"
        student_tokens = [w.lower() for w in student_doc.replace("/", " ").replace("-", " ").split()]

        # Compute TF-IDF Cosine Similarities
        student_tfidf = self.tfidf_vectorizer.transform([student_doc])
        tfidf_sims = cosine_similarity(student_tfidf, self.tfidf_matrix)[0]

        # Compute BM25 Scores
        bm25_raw_scores = self.bm25_model.get_scores(student_tokens)
        max_bm25 = max(bm25_raw_scores) if max(bm25_raw_scores) > 0 else 1.0
        bm25_normalized = [s / max_bm25 for s in bm25_raw_scores]

        recommendations = []

        for idx, job in enumerate(self.internships):
            # Domain and work type filtering
            if target_domain and target_domain.lower() != "all" and job["domain"].lower() != target_domain.lower():
                continue
            if work_type_filter and work_type_filter.lower() != "all" and job["work_type"].lower() != work_type_filter.lower():
                continue

            job_req = [normalize_skill(s) for s in job.get("required_skills", [])]
            job_pref = [normalize_skill(s) for s in job.get("preferred_skills", [])]

            matched_req = [s for s in job_req if s in normalized_student_skills]
            missing_req = [s for s in job_req if s not in normalized_student_skills]
            matched_pref = [s for s in job_pref if s in normalized_student_skills]
            missing_pref = [s for s in job_pref if s not in normalized_student_skills]

            # 1. Skill Overlap Score (0 to 1)
            req_ratio = len(matched_req) / len(job_req) if job_req else 1.0
            pref_ratio = len(matched_pref) / len(job_pref) if job_pref else 1.0
            # Required skills have 80% weight within the skill score component
            skill_score = (0.80 * req_ratio) + (0.20 * pref_ratio)

            # 2. Semantic TF-IDF Similarity (0 to 1)
            semantic_score = float(tfidf_sims[idx])

            # 3. BM25 Salience Score (0 to 1)
            bm25_score = float(bm25_normalized[idx])

            # Composite Calibrated Match Score:
            # 50% Skill match, 35% Semantic context, 15% BM25 keyword salience
            raw_composite = (0.50 * skill_score) + (0.35 * semantic_score) + (0.15 * bm25_score)

            # Calibrate to intuitive 0 - 100 percentage
            # High penalty if missing all required skills; reward if meeting 100% required skills
            match_percentage = self._calibrate_score(raw_composite, req_ratio, pref_ratio)

            if match_percentage < min_match_score:
                continue

            # Tier classification
            tier, tier_color, tier_badge = self._get_tier_info(match_percentage)

            # Generate key strengths
            strengths = self._generate_strengths(matched_req, matched_pref, req_ratio)

            recommendations.append({
                "internship": job,
                "match_score": round(match_percentage, 1),
                "tier": tier,
                "tier_color": tier_color,
                "tier_badge": tier_badge,
                "matched_required": matched_req,
                "missing_required": missing_req,
                "matched_preferred": matched_pref,
                "missing_preferred": missing_pref,
                "score_breakdown": {
                    "skill_overlap": round(skill_score * 100, 1),
                    "semantic_similarity": round(semantic_score * 100, 1),
                    "bm25_salience": round(bm25_score * 100, 1)
                },
                "key_strengths": strengths,
                "growth_potential": f"{len(missing_req)} required skill(s) away from peak qualification" if missing_req else "Candidate possesses 100% of core technical requirements!"
            })

        # Sort descending by match score
        recommendations.sort(key=lambda r: r["match_score"], reverse=True)
        return recommendations[:top_k]

    @staticmethod
    def _calibrate_score(raw_composite: float, req_ratio: float, pref_ratio: float) -> float:
        """
        Calibrates composite score into a clean 10-99% curve reflecting real-world hiring criteria.
        """
        # If candidate meets 100% required skills, score should be >= 86%
        if req_ratio == 1.0:
            base = 86.0 + (pref_ratio * 12.0)
            score = max(base, raw_composite * 100)
        elif req_ratio >= 0.75:
            score = 75.0 + (req_ratio - 0.75) * 40.0 + (pref_ratio * 8.0)
        elif req_ratio >= 0.50:
            score = 58.0 + (req_ratio - 0.50) * 45.0 + (pref_ratio * 8.0)
        elif req_ratio >= 0.25:
            score = 38.0 + (req_ratio - 0.25) * 50.0 + (raw_composite * 20.0)
        else:
            score = 15.0 + (req_ratio * 60.0) + (raw_composite * 25.0)

        return min(99.0, max(12.0, score))

    @staticmethod
    def _get_tier_info(score: float) -> Tuple[str, str, str]:
        """Returns readable tier title, accent color, and status label."""
        if score >= 88.0:
            return "Exceptional Fit", "#10B981", "🌟 Top Match"
        elif score >= 75.0:
            return "Strong Fit", "#6366F1", "🎯 Strong Fit"
        elif score >= 60.0:
            return "Moderate Fit", "#F59E0B", "📈 Good Upskill Fit"
        else:
            return "Reach Opportunity", "#64748B", "💡 Upskill Target"

    @staticmethod
    def _generate_strengths(matched_req: List[str], matched_pref: List[str], req_ratio: float) -> List[str]:
        strengths = []
        if req_ratio >= 1.0:
            strengths.append("Meets 100% of core required technical competencies")
        elif req_ratio >= 0.6:
            strengths.append(f"Strong foundation in core stack: {', '.join(matched_req[:3])}")
        
        if matched_pref:
            strengths.append(f"Bonus qualification advantage: {', '.join(matched_pref[:2])}")
        
        if not strengths:
            if matched_req:
                strengths.append(f"Direct experience with {', '.join(matched_req)}")
            else:
                strengths.append("Foundational skills transferable to this role")

        return strengths
