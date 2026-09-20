import os
import sys
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename

# =========================================================
# PROJECT ROOT FIX
# =========================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# =========================================================
# IMPORTS
# =========================================================

from app.resume_parser import extract_text_from_pdf
from app.matcher import (
    extract_skills,
    calculate_match,
    calculate_text_similarity,
    calculate_overall_score
)

from database.database import (
    save_analysis,
    get_analysis_history
)

# =========================================================
# FLASK APP
# =========================================================

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, "uploads")
ALLOWED_EXTENSIONS = {"pdf"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# =========================================================
# HELPERS
# =========================================================

def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


# =========================================================
# HOME / DASHBOARD
# =========================================================

@app.route("/")
def home():
    return render_template("index.html")


# =========================================================
# ANALYSIS HISTORY
# =========================================================

@app.route("/history")
def history():

    records = get_analysis_history()

    rows = ""

    for record in records:
        rows += f"""
        <tr>
            <td>{record["resume_name"]}</td>
            <td>{record["overall_score"]}%</td>
            <td>{record["skill_score"]}%</td>
            <td>{record["nlp_score"]}%</td>
            <td>{record["analyzed_at"]}</td>
        </tr>
        """

    if not rows:
        rows = """
        <tr>
            <td colspan="5" style="text-align:center;">
                No analysis history available yet.
            </td>
        </tr>
        """

    return f"""
<!DOCTYPE html>
<html lang="en">

<head>

<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>ResumeAI | History</title>

<style>

* {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}

body {{
    font-family: Inter, Arial, Helvetica, sans-serif;
    background:
        radial-gradient(
            circle at 10% 10%,
            rgba(124,58,237,0.14),
            transparent 30%
        ),
        radial-gradient(
            circle at 90% 20%,
            rgba(37,99,235,0.12),
            transparent 30%
        ),
        #080b14;
    color: #f8fafc;
    min-height: 100vh;
}}

.app {{
    display: flex;
    min-height: 100vh;
}}

.sidebar {{
    width: 255px;
    background: rgba(12,16,28,0.96);
    border-right: 1px solid rgba(255,255,255,0.07);
    padding: 28px 18px;
    display: flex;
    flex-direction: column;
    position: fixed;
    top: 0;
    bottom: 0;
    left: 0;
}}

.brand {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 45px;
}}

.brand-icon {{
    width: 42px;
    height: 42px;
    border-radius: 13px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg,#7c3aed,#2563eb);
    font-size: 22px;
    box-shadow: 0 8px 25px rgba(124,58,237,0.35);
}}

.brand h2 {{
    font-size: 19px;
}}

.brand span {{
    display: block;
    color: #7f8aa3;
    font-size: 11px;
    margin-top: 3px;
}}

.nav-item {{
    display: flex;
    align-items: center;
    gap: 13px;
    padding: 13px 15px;
    margin-bottom: 8px;
    color: #8f9ab0;
    text-decoration: none;
    border-radius: 12px;
    transition: 0.25s;
}}

.nav-item:hover,
.nav-item.active {{
    color: white;
    background: linear-gradient(
        90deg,
        rgba(124,58,237,0.20),
        rgba(37,99,235,0.08)
    );
}}

.nav-item span {{
    font-size: 19px;
}}

.sidebar-bottom {{
    margin-top: auto;
}}

.ai-status {{
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 14px;
    border-radius: 14px;
    background: rgba(255,255,255,0.035);
    border: 1px solid rgba(255,255,255,0.06);
}}

.status-dot {{
    width: 9px;
    height: 9px;
    border-radius: 50%;
    background: #22c55e;
    box-shadow: 0 0 12px #22c55e;
}}

.ai-status strong {{
    display: block;
    font-size: 13px;
}}

.ai-status small {{
    color: #64748b;
    font-size: 11px;
}}

.sidebar-footer {{
    color: #475569;
    font-size: 11px;
    text-align: center;
    margin-top: 18px;
}}

.main {{
    margin-left: 255px;
    width: calc(100% - 255px);
    padding: 34px 42px 50px;
}}

.topbar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 32px;
}}

.eyebrow {{
    color: #8b5cf6;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 2px;
}}

h1 {{
    font-size: 30px;
    margin-top: 7px;
}}

.subtitle {{
    color: #7f8aa3;
    margin-top: 6px;
    font-size: 14px;
}}

.profile {{
    display: flex;
    align-items: center;
    gap: 11px;
}}

.profile-avatar {{
    width: 42px;
    height: 42px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg,#7c3aed,#2563eb);
    font-weight: 800;
}}

.profile strong {{
    display: block;
    font-size: 13px;
}}

.profile small {{
    color: #64748b;
}}

.card {{
    background: rgba(15,20,34,0.88);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 20px;
    padding: 24px;
    box-shadow: 0 15px 45px rgba(0,0,0,0.18);
}}

.table-wrap {{
    overflow-x: auto;
}}

table {{
    width: 100%;
    border-collapse: collapse;
}}

th,
td {{
    padding: 16px 14px;
    text-align: left;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    font-size: 13px;
}}

th {{
    color: #a78bfa;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1px;
}}

td {{
    color: #cbd5e1;
}}

.score {{
    color: #a78bfa;
    font-weight: 800;
}}

.button {{
    display: inline-block;
    margin-top: 22px;
    text-decoration: none;
    color: white;
    padding: 13px 20px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 800;
    background: linear-gradient(135deg,#7c3aed,#2563eb);
}}

@media(max-width:900px) {{
    .sidebar {{
        width: 75px;
        padding: 20px 10px;
    }}

    .brand h2,
    .brand span,
    .ai-status div,
    .sidebar-footer {{
        display: none;
    }}

    .main {{
        margin-left: 75px;
        width: calc(100% - 75px);
        padding: 25px;
    }}
}}

@media(max-width:600px) {{
    .main {{
        padding: 18px;
    }}

    .profile {{
        display: none;
    }}
}}

</style>

</head>

<body>

<div class="app">

<aside class="sidebar">

    <div class="brand">

        <div class="brand-icon">✦</div>

        <div>
            <h2>ResumeAI</h2>
            <span>AI Career Intelligence</span>
        </div>

    </div>

    <nav>

        <a href="/" class="nav-item">
            <span>⌂</span>
            Dashboard
        </a>

        <a href="/history" class="nav-item active">
            <span>◷</span>
            Analysis History
        </a>

    </nav>

    <div class="sidebar-bottom">

        <div class="ai-status">

            <div class="status-dot"></div>

            <div>
                <strong>AI Engine</strong>
                <small>Online & Ready</small>
            </div>

        </div>

        <div class="sidebar-footer">
            CSE Project
        </div>

    </div>

</aside>

<main class="main">

<header class="topbar">

    <div>
        <span class="eyebrow">AI RESUME INTELLIGENCE</span>

        <h1>Analysis History</h1>

        <p class="subtitle">
            Previous resume analysis reports
        </p>
    </div>

    <div class="profile">

        <div class="profile-avatar">AR</div>

        <div>
            <strong>Ahmed Raza</strong>
            <small>Developer</small>
        </div>

    </div>

</header>

<section class="card">

    <div class="table-wrap">

        <table>

            <thead>

                <tr>
                    <th>Resume</th>
                    <th>Overall</th>
                    <th>Technical</th>
                    <th>Semantic AI</th>
                    <th>Analyzed At</th>
                </tr>

            </thead>

            <tbody>

                {rows}

            </tbody>

        </table>

    </div>

    <a href="/" class="button">
        ← Analyze New Resume
    </a>

</section>

</main>

</div>

</body>

</html>
"""


# =========================================================
# ANALYZE RESUME
# =========================================================

@app.route("/analyze", methods=["POST"])
def analyze():

    # -----------------------------------------------------
    # 1. CHECK FILE
    # -----------------------------------------------------

    if "resume" not in request.files:
        return "No resume file uploaded."

    file = request.files["resume"]

    if file.filename == "":
        return "Please select a PDF resume."

    if not allowed_file(file.filename):
        return "Only PDF files are supported."

    # -----------------------------------------------------
    # 2. SAVE RESUME
    # -----------------------------------------------------

    filename = secure_filename(file.filename)

    file_path = os.path.join(
        UPLOAD_FOLDER,
        filename
    )

    file.save(file_path)

    # -----------------------------------------------------
    # 3. GET JOB DESCRIPTION
    # -----------------------------------------------------

    job_description = request.form.get(
        "job_description",
        ""
    ).strip()

    if not job_description:
        return "Please enter a job description."

    # -----------------------------------------------------
    # 4. EXTRACT RESUME TEXT
    # -----------------------------------------------------

    resume_text = extract_text_from_pdf(
        file_path
    )

    if not resume_text:
        return "Could not extract text from the PDF."

    # -----------------------------------------------------
    # 5. EXTRACT SKILLS
    # -----------------------------------------------------

    resume_skills = extract_skills(
        resume_text
    )

    job_skills = extract_skills(
        job_description
    )

    # -----------------------------------------------------
    # 6. TECHNICAL MATCH
    # -----------------------------------------------------

    match_result = calculate_match(
        resume_skills,
        job_skills
    )

    skill_score = match_result["score"]
    matched_skills = match_result["matched_skills"]
    missing_skills = match_result["missing_skills"]

    # -----------------------------------------------------
    # 7. SEMANTIC AI SIMILARITY
    # -----------------------------------------------------

    nlp_score = calculate_text_similarity(
        resume_text,
        job_description
    )

    # -----------------------------------------------------
    # 8. OVERALL SCORE
    # -----------------------------------------------------

    overall_score = calculate_overall_score(
        skill_score,
        nlp_score
    )

    # -----------------------------------------------------
    # 9. SAVE ANALYSIS
    # -----------------------------------------------------

    save_analysis(
        filename,
        overall_score,
        skill_score,
        nlp_score,
        matched_skills,
        missing_skills
    )

    # -----------------------------------------------------
    # 10. MATCHED SKILLS HTML
    # -----------------------------------------------------

    if matched_skills:

        matched_html = ""

        for skill in matched_skills:

            matched_html += f"""
            <div class="skill matched">
                ✓ {skill.title()}
            </div>
            """

    else:

        matched_html = """
        <div class="empty">
            No matching technical skills found.
        </div>
        """

    # -----------------------------------------------------
    # 11. MISSING SKILLS HTML
    # -----------------------------------------------------

    if missing_skills:

        missing_html = ""

        for skill in missing_skills:

            missing_html += f"""
            <div class="skill missing">
                + {skill.title()}
            </div>
            """

    else:

        missing_html = """
        <div class="empty">
            No major missing technical skills detected.
        </div>
        """

    # -----------------------------------------------------
    # 12. AI RECOMMENDATIONS
    # -----------------------------------------------------

    recommendations = {

        "python":
            "Strengthen Python by building real-world applications and practicing problem solving.",

        "java":
            "Practice Java OOP, collections, exception handling and DSA for placement preparation.",

        "flask":
            "Build REST APIs with Flask and connect them with SQL databases.",

        "mysql":
            "Practice SQL queries, joins, indexes and database design using MySQL.",

        "sql":
            "Improve SQL through joins, subqueries, aggregation and database design problems.",

        "rest api":
            "Learn REST API architecture, HTTP methods, JSON, authentication and API testing.",

        "git":
            "Practice Git commands, branching, merging and collaborative version control.",

        "github":
            "Maintain projects on GitHub with clean README files, commits and repositories.",

        "machine learning":
            "Learn supervised learning, model evaluation and practical ML projects.",

        "pandas":
            "Practice data cleaning, filtering, grouping and analysis using Pandas.",

        "numpy":
            "Practice arrays, vectorized operations and numerical computing with NumPy.",

        "scikit-learn":
            "Build small ML projects using preprocessing, training and model evaluation.",

        "docker":
            "Learn Docker images, containers, Dockerfiles and basic application deployment.",

        "html":
            "Improve semantic HTML and build responsive project interfaces.",

        "css":
            "Practice responsive layouts, Flexbox, Grid and modern UI design.",

        "javascript":
            "Strengthen JavaScript fundamentals and DOM manipulation."
    }

    recommendations_html = ""

    for skill in missing_skills:

        recommendation = recommendations.get(
            skill,
            f"Add practical experience with {skill.title()} through a small project."
        )

        recommendations_html += f"""
        <div class="recommendation">

            <div class="recommendation-title">
                {skill.title()}
            </div>

            <div class="recommendation-text">
                {recommendation}
            </div>

        </div>
        """

    if not recommendations_html:

        recommendations_html = """
        <div class="recommendation">

            <div class="recommendation-title">
                Great Skill Coverage
            </div>

            <div class="recommendation-text">
                Your resume contains the main technical skills
                detected from the provided job description.
            </div>

        </div>
        """

    # -----------------------------------------------------
    # 13. RESUME SKILLS HTML
    # -----------------------------------------------------

    if resume_skills:

        resume_skills_html = ""

        for skill in resume_skills:

            resume_skills_html += f"""
            <div class="resume-skill">
                {skill.title()}
            </div>
            """

    else:

        resume_skills_html = """
        <div class="empty">
            No technical skills detected.
        </div>
        """

    # -----------------------------------------------------
    # 14. SCORE MESSAGE
    # -----------------------------------------------------

    if overall_score >= 80:

        score_message = "Strong overall match"

    elif overall_score >= 60:

        score_message = "Good overall match"

    elif overall_score >= 40:

        score_message = "Moderate overall match"

    else:

        score_message = "Low overall match"

    # =====================================================
    # 15. PREMIUM RESULT DASHBOARD
    # =====================================================

    return f"""
<!DOCTYPE html>

<html lang="en">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>ResumeAI | Analysis</title>

<style>

* {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}

body {{
    font-family:
        Inter,
        Arial,
        Helvetica,
        sans-serif;

    background:
        radial-gradient(
            circle at 10% 10%,
            rgba(124,58,237,0.14),
            transparent 30%
        ),
        radial-gradient(
            circle at 90% 20%,
            rgba(37,99,235,0.12),
            transparent 30%
        ),
        #080b14;

    color: #f8fafc;
    min-height: 100vh;
}}

.app {{
    display: flex;
    min-height: 100vh;
}}

.sidebar {{
    width: 255px;
    background: rgba(12,16,28,0.96);
    border-right: 1px solid rgba(255,255,255,0.07);
    padding: 28px 18px;
    display: flex;
    flex-direction: column;
    position: fixed;
    top: 0;
    bottom: 0;
    left: 0;
}}

.brand {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 45px;
}}

.brand-icon {{
    width: 42px;
    height: 42px;
    border-radius: 13px;

    display: flex;
    align-items: center;
    justify-content: center;

    background:
        linear-gradient(
            135deg,
            #7c3aed,
            #2563eb
        );

    font-size: 22px;

    box-shadow:
        0 8px 25px rgba(124,58,237,0.35);
}}

.brand h2 {{
    font-size: 19px;
}}

.brand span {{
    display: block;
    color: #7f8aa3;
    font-size: 11px;
    margin-top: 3px;
}}

.nav-item {{
    display: flex;
    align-items: center;
    gap: 13px;

    padding: 13px 15px;
    margin-bottom: 8px;

    color: #8f9ab0;
    text-decoration: none;

    border-radius: 12px;
    transition: 0.25s;
}}

.nav-item:hover,
.nav-item.active {{
    color: white;

    background:
        linear-gradient(
            90deg,
            rgba(124,58,237,0.20),
            rgba(37,99,235,0.08)
        );
}}

.nav-item span {{
    font-size: 19px;
}}

.sidebar-bottom {{
    margin-top: auto;
}}

.ai-status {{
    display: flex;
    align-items: center;
    gap: 10px;

    padding: 14px;
    border-radius: 14px;

    background: rgba(255,255,255,0.035);
    border: 1px solid rgba(255,255,255,0.06);
}}

.status-dot {{
    width: 9px;
    height: 9px;
    border-radius: 50%;

    background: #22c55e;

    box-shadow:
        0 0 12px #22c55e;
}}

.ai-status strong {{
    display: block;
    font-size: 13px;
}}

.ai-status small {{
    color: #64748b;
    font-size: 11px;
}}

.sidebar-footer {{
    color: #475569;
    font-size: 11px;
    text-align: center;
    margin-top: 18px;
}}

.main {{
    margin-left: 255px;
    width: calc(100% - 255px);
    padding: 34px 42px 50px;
}}

.topbar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 32px;
}}

.eyebrow {{
    color: #8b5cf6;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 2px;
}}

.topbar h1 {{
    font-size: 30px;
    margin-top: 7px;
}}

.topbar p {{
    color: #7f8aa3;
    margin-top: 6px;
    font-size: 14px;
}}

.profile {{
    display: flex;
    align-items: center;
    gap: 11px;
}}

.profile-avatar {{
    width: 42px;
    height: 42px;
    border-radius: 50%;

    display: flex;
    align-items: center;
    justify-content: center;

    background:
        linear-gradient(
            135deg,
            #7c3aed,
            #2563eb
        );

    font-weight: 800;
}}

.profile strong {{
    display: block;
    font-size: 13px;
}}

.profile small {{
    color: #64748b;
}}

.result-hero {{
    padding: 28px;

    border-radius: 22px;

    background:
        linear-gradient(
            135deg,
            rgba(124,58,237,0.17),
            rgba(37,99,235,0.09)
        );

    border: 1px solid rgba(139,92,246,0.20);

    margin-bottom: 22px;
}}

.hero-badge {{
    display: inline-block;

    padding: 7px 12px;
    border-radius: 20px;

    background: rgba(124,58,237,0.15);
    color: #c4b5fd;

    font-size: 11px;
    font-weight: 800;
    letter-spacing: 1px;
}}

.result-hero h2 {{
    margin-top: 15px;
    font-size: 25px;
}}

.result-hero p {{
    color: #8f9ab0;
    margin-top: 7px;
}}

.score-grid {{
    display: grid;
    grid-template-columns:
        1.4fr 1fr 1fr;

    gap: 18px;
    margin-bottom: 22px;
}}

.card {{
    background:
        rgba(15,20,34,0.88);

    border:
        1px solid rgba(255,255,255,0.07);

    border-radius: 20px;

    padding: 24px;

    box-shadow:
        0 15px 45px rgba(0,0,0,0.18);
}}

.card-title {{
    color: #8f9ab0;
    font-size: 12px;
    font-weight: 700;
    margin-bottom: 17px;
}}

.score-main {{
    display: flex;
    align-items: center;
    gap: 25px;
}}

.score-ring {{
    width: 145px;
    height: 145px;

    border-radius: 50%;

    display: flex;
    align-items: center;
    justify-content: center;

    background:
        conic-gradient(
            #8b5cf6 {overall_score}%,
            #20263a {overall_score}% 100%
        );

    position: relative;
}}

.score-ring::after {{
    content: "";
    position: absolute;

    width: 113px;
    height: 113px;

    border-radius: 50%;
    background: #0d1220;
}}

.score-number {{
    position: relative;
    z-index: 2;

    font-size: 30px;
    font-weight: 900;
}}

.score-info h3 {{
    font-size: 18px;
    margin-bottom: 7px;
}}

.score-info p {{
    color: #8f9ab0;
    font-size: 12px;
    line-height: 1.6;
}}

.score-status {{
    display: inline-block;
    margin-top: 12px;

    color: #a78bfa;
    background: rgba(139,92,246,0.12);

    padding: 6px 10px;
    border-radius: 8px;

    font-size: 11px;
    font-weight: 700;
}}

.metric-value {{
    font-size: 34px;
    font-weight: 900;
    margin-bottom: 8px;
}}

.metric-purple {{
    color: #a78bfa;
}}

.metric-blue {{
    color: #60a5fa;
}}

.metric-label {{
    color: #8f9ab0;
    font-size: 12px;
}}

.progress {{
    height: 7px;
    background: #20263a;
    border-radius: 20px;
    margin-top: 17px;
    overflow: hidden;
}}

.progress-bar {{
    height: 100%;
    border-radius: 20px;

    background:
        linear-gradient(
            90deg,
            #7c3aed,
            #3b82f6
        );
}}

.content-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;

    gap: 20px;
    margin-bottom: 20px;
}}

.section-heading {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}}

.section-heading h2 {{
    font-size: 17px;
}}

.count {{
    color: #64748b;
    font-size: 11px;
}}

.skills {{
    display: flex;
    flex-wrap: wrap;
    gap: 9px;
}}

.skill {{
    padding: 9px 13px;
    border-radius: 10px;

    display: flex;
    align-items: center;
    gap: 7px;

    font-size: 12px;
    font-weight: 700;
}}

.skill.matched {{
    color: #4ade80;
    background: rgba(34,197,94,0.10);
    border: 1px solid rgba(34,197,94,0.18);
}}

.skill.missing {{
    color: #fb7185;
    background: rgba(244,63,94,0.10);
    border: 1px solid rgba(244,63,94,0.18);
}}

.recommendations {{
    display: grid;
    gap: 11px;
}}

.recommendation {{
    padding: 15px;
    border-radius: 13px;

    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.055);

    transition: 0.2s;
}}

.recommendation:hover {{
    transform: translateY(-2px);
    border-color: rgba(139,92,246,0.35);
}}

.recommendation-title {{
    color: #c4b5fd;
    font-weight: 800;
    font-size: 13px;
    margin-bottom: 5px;
}}

.recommendation-text {{
    color: #7f8aa3;
    font-size: 12px;
    line-height: 1.5;
}}

.resume-skills {{
    display: flex;
    flex-wrap: wrap;
    gap: 9px;
}}

.resume-skill {{
    padding: 8px 12px;
    border-radius: 9px;

    color: #93c5fd;

    background: rgba(59,130,246,0.09);
    border: 1px solid rgba(59,130,246,0.15);

    font-size: 11px;
    font-weight: 700;
}}

.insights {{
    display: grid;
    grid-template-columns:
        repeat(3,1fr);

    gap: 14px;
}}

.insight {{
    padding: 17px;
    border-radius: 14px;

    background: rgba(255,255,255,0.025);
}}

.insight-icon {{
    font-size: 20px;
    margin-bottom: 10px;
}}

.insight strong {{
    display: block;
    font-size: 13px;
}}

.insight span {{
    display: block;
    color: #64748b;
    font-size: 11px;
    margin-top: 5px;
}}

.actions {{
    display: flex;
    gap: 12px;
    margin-top: 25px;
}}

.button {{
    text-decoration: none;
    padding: 13px 20px;
    border-radius: 12px;

    font-size: 12px;
    font-weight: 800;

    transition: 0.2s;
}}

.primary {{
    color: white;

    background:
        linear-gradient(
            135deg,
            #7c3aed,
            #2563eb
        );

    box-shadow:
        0 8px 25px rgba(99,102,241,0.25);
}}

.secondary {{
    color: #cbd5e1;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.08);
}}

.button:hover {{
    transform: translateY(-2px);
}}

.empty {{
    color: #64748b;
    font-size: 12px;
    padding: 12px 0;
}}

@media(max-width:900px) {{

    .sidebar {{
        width: 75px;
        padding: 20px 10px;
    }}

    .brand h2,
    .brand span,
    .ai-status div,
    .sidebar-footer {{
        display: none;
    }}

    .nav-item {{
        justify-content: center;
        font-size: 0;
    }}

    .nav-item span {{
        font-size: 20px;
    }}

    .main {{
        margin-left: 75px;
        width: calc(100% - 75px);
        padding: 25px;
    }}

    .score-grid,
    .content-grid {{
        grid-template-columns: 1fr;
    }}

    .insights {{
        grid-template-columns: 1fr;
    }}
}}

@media(max-width:600px) {{

    .main {{
        padding: 18px;
    }}

    .topbar {{
        align-items: flex-start;
    }}

    .profile {{
        display: none;
    }}

    .score-main {{
        flex-direction: column;
        align-items: flex-start;
    }}

    .score-ring {{
        margin: auto;
    }}

    .actions {{
        flex-direction: column;
    }}

    .button {{
        text-align: center;
    }}
}}

</style>

</head>

<body>

<div class="app">

<aside class="sidebar">

    <div class="brand">

        <div class="brand-icon">
            ✦
        </div>

        <div>

            <h2>ResumeAI</h2>

            <span>
                AI Career Intelligence
            </span>

        </div>

    </div>

    <nav>

        <a href="/" class="nav-item">

            <span>⌂</span>

            Dashboard

        </a>

        <a href="/history" class="nav-item">

            <span>◷</span>

            Analysis History

        </a>

    </nav>

    <div class="sidebar-bottom">

        <div class="ai-status">

            <div class="status-dot"></div>

            <div>

                <strong>
                    AI Engine
                </strong>

                <small>
                    Online & Ready
                </small>

            </div>

        </div>

        <div class="sidebar-footer">
            CSE Project
        </div>

    </div>

</aside>

<main class="main">

<header class="topbar">

    <div>

        <span class="eyebrow">
            AI RESUME INTELLIGENCE
        </span>

        <h1>
            Analysis Results
        </h1>

        <p>
            Resume intelligence report generated by ResumeAI
        </p>

    </div>

    <div class="profile">

        <div class="profile-avatar">
            AR
        </div>

        <div>

            <strong>
                Ahmed Raza
            </strong>

            <small>
                Developer
            </small>

        </div>

    </div>

</header>

<section class="result-hero">

    <span class="hero-badge">
        ✨ AI POWERED ANALYSIS
    </span>

    <h2>
        Your resume has been analyzed.
    </h2>

    <p>
        Here is how well your resume matches the job description.
    </p>

</section>

<section class="score-grid">

    <div class="card">

        <div class="card-title">
            🎯 OVERALL AI MATCH
        </div>

        <div class="score-main">

            <div class="score-ring">

                <div class="score-number">
                    {overall_score}%
                </div>

            </div>

            <div class="score-info">

                <h3>
                    {score_message}
                </h3>

                <p>
                    Your resume compatibility
                    with this job description
                    based on skills and semantic
                    relevance.
                </p>

                <span class="score-status">
                    AI SCORE
                </span>

            </div>

        </div>

    </div>

    <div class="card">

        <div class="card-title">
            🧠 TECHNICAL SKILL MATCH
        </div>

        <div class="metric-value metric-purple">
            {skill_score}%
        </div>

        <div class="metric-label">
            Required skills found
        </div>

        <div class="progress">

            <div
                class="progress-bar"
                style="width:{skill_score}%">
            </div>

        </div>

    </div>

    <div class="card">

        <div class="card-title">
            🤖 SEMANTIC AI SIMILARITY
        </div>

        <div class="metric-value metric-blue">
            {nlp_score}%
        </div>

        <div class="metric-label">
            Resume vs job relevance
        </div>

        <div class="progress">

            <div
                class="progress-bar"
                style="width:{nlp_score}%">
            </div>

        </div>

    </div>

</section>

<section class="content-grid">

    <div class="card">

        <div class="section-heading">

            <h2>
                ✅ Matched Skills
            </h2>

            <span class="count">
                {len(matched_skills)} found
            </span>

        </div>

        <div class="skills">
            {matched_html}
        </div>

    </div>

    <div class="card">

        <div class="section-heading">

            <h2>
                ⚠️ Missing Skills
            </h2>

            <span class="count">
                {len(missing_skills)} required
            </span>

        </div>

        <div class="skills">
            {missing_html}
        </div>

    </div>

</section>

<section class="card">

    <div class="section-heading">

        <h2>
            💡 AI Learning Recommendations
        </h2>

        <span class="count">
            Personalized
        </span>

    </div>

    <div class="recommendations">
        {recommendations_html}
    </div>

</section>

<br>

<section class="card">

    <div class="section-heading">

        <h2>
            🧠 Skills Detected in Resume
        </h2>

        <span class="count">
            {len(resume_skills)} skills
        </span>

    </div>

    <div class="resume-skills">
        {resume_skills_html}
    </div>

</section>

<br>

<section class="card">

    <div class="section-heading">

        <h2>
            📊 Resume Intelligence
        </h2>

    </div>

    <div class="insights">

        <div class="insight">

            <div class="insight-icon">
                📄
            </div>

            <strong>
                Resume Analyzed
            </strong>

            <span>
                {filename}
            </span>

        </div>

        <div class="insight">

            <div class="insight-icon">
                ✅
            </div>

            <strong>
                Skills Matched
            </strong>

            <span>
                {len(matched_skills)}
                technical skills
            </span>

        </div>

        <div class="insight">

            <div class="insight-icon">
                📚
            </div>

            <strong>
                Skills To Improve
            </strong>

            <span>
                {len(missing_skills)}
                skills identified
            </span>

        </div>

    </div>

</section>

<div class="actions">

    <a
        href="/"
        class="button primary"
    >
        ← Analyze Another Resume
    </a>

    <a
        href="/history"
        class="button secondary"
    >
        📊 Analysis History
    </a>

</div>

</main>

</div>

</body>

</html>
"""


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":
    app.run(
        debug=True
    )
