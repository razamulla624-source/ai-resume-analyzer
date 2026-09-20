import os
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# =========================================================
# OPTIONAL AI MODEL
# =========================================================
# Local PC:
#   Uses Sentence Transformer exactly like before.
#
# Render Free:
#   Heavy transformer model is NOT loaded.
#   Lightweight TF-IDF similarity is used instead.
# =========================================================

IS_RENDER = os.getenv("RENDER", "").lower() == "true"

model = None

if not IS_RENDER:
    try:
        from sentence_transformers import SentenceTransformer, util

        model = SentenceTransformer(
            "all-MiniLM-L6-v2"
        )

        print("AI Model loaded: all-MiniLM-L6-v2")

    except Exception as e:
        print("Sentence Transformer unavailable:", e)
        model = None


# =========================================================
# SKILLS DATABASE
# =========================================================

SKILLS = [

    "python",
    "java",
    "c",
    "c++",
    "javascript",
    "html",
    "css",
    "react",
    "flask",
    "django",
    "mysql",
    "sql",
    "mongodb",
    "pandas",
    "numpy",
    "scikit-learn",
    "machine learning",
    "deep learning",
    "nlp",
    "opencv",
    "git",
    "github",
    "docker",
    "power bi",
    "tableau",
    "rest api",
    "aws"

]


# =========================================================
# EXTRACT SKILLS
# =========================================================

def extract_skills(text):

    text = text.lower()

    found_skills = []

    for skill in SKILLS:

        pattern = r"\b" + re.escape(skill) + r"\b"

        if re.search(pattern, text):

            if skill not in found_skills:

                found_skills.append(skill)

    return found_skills


# =========================================================
# TECHNICAL SKILL MATCH
# =========================================================

def calculate_match(resume_skills, job_skills):

    resume_set = set(resume_skills)

    job_set = set(job_skills)

    matched_skills = sorted(
        resume_set.intersection(job_set)
    )

    missing_skills = sorted(
        job_set - resume_set
    )

    if len(job_set) == 0:

        skill_score = 0

    else:

        skill_score = (
            len(matched_skills)
            /
            len(job_set)
        ) * 100

    return {

        "score": round(
            skill_score,
            2
        ),

        "matched_skills":
            matched_skills,

        "missing_skills":
            missing_skills

    }


# =========================================================
# SEMANTIC / TEXT SIMILARITY
# =========================================================

def calculate_text_similarity(
    resume_text,
    job_description
):

    try:

        # -------------------------------------------------
        # LOCAL COMPUTER
        # -------------------------------------------------
        # Keep the original Sentence Transformer AI.
        # This is exactly the same model you were using.
        # -------------------------------------------------

        if model is not None:

            resume_embedding = model.encode(
                resume_text,
                convert_to_tensor=True
            )

            job_embedding = model.encode(
                job_description,
                convert_to_tensor=True
            )

            similarity = util.cos_sim(
                resume_embedding,
                job_embedding
            )

            similarity_score = (
                float(similarity[0][0])
                * 100
            )

            similarity_score = max(
                0,
                min(
                    100,
                    similarity_score
                )
            )

            return round(
                similarity_score,
                2
            )

        # -------------------------------------------------
        # RENDER FREE
        # -------------------------------------------------
        # Lightweight text similarity.
        # Does not load PyTorch / Sentence Transformer.
        # -------------------------------------------------

        vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=5000
        )

        vectors = vectorizer.fit_transform([
            resume_text,
            job_description
        ])

        similarity_score = cosine_similarity(
            vectors[0:1],
            vectors[1:2]
        )[0][0] * 100

        similarity_score = max(
            0,
            min(
                100,
                similarity_score
            )
        )

        return round(
            similarity_score,
            2
        )

    except Exception as e:

        print(
            "Text similarity error:",
            e
        )

        return 0.0


# =========================================================
# OVERALL AI SCORE
# =========================================================

def calculate_overall_score(
    skill_score,
    text_similarity
):

    overall_score = (

        skill_score * 0.70

        +

        text_similarity * 0.30

    )

    return round(
        overall_score,
        2
    )