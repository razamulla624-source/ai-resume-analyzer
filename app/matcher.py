import re

from sentence_transformers import SentenceTransformer, util


# ==========================================
# AI MODEL
# ==========================================

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


# ==========================================
# SKILLS DATABASE
# ==========================================

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


# ==========================================
# EXTRACT SKILLS
# ==========================================

def extract_skills(text):

    text = text.lower()

    found_skills = []

    for skill in SKILLS:

        pattern = r"\b" + re.escape(skill) + r"\b"

        if re.search(pattern, text):

            if skill not in found_skills:

                found_skills.append(skill)

    return found_skills


# ==========================================
# TECHNICAL SKILL MATCH
# ==========================================

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


# ==========================================
# SEMANTIC AI SIMILARITY
# ==========================================

def calculate_text_similarity(
    resume_text,
    job_description
):

    try:

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

        # Keep score between 0 and 100
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
            "Semantic similarity error:",
            e
        )

        return 0.0


# ==========================================
# OVERALL AI SCORE
# ==========================================

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