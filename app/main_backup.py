import os
import sys

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
import os

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


app = Flask(__name__)


UPLOAD_FOLDER = "uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


# ==========================================
# HOME
# ==========================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# ==========================================
# ANALYSIS HISTORY
# ==========================================

@app.route("/history")
def history():

    records = get_analysis_history()

    history_html = ""

    for record in records:

        history_html += f"""
        <tr>

            <td>
                {record["resume_name"]}
            </td>

            <td>
                {record["overall_score"]}%
            </td>

            <td>
                {record["skill_score"]}%
            </td>

            <td>
                {record["nlp_score"]}%
            </td>

            <td>
                {record["analyzed_at"]}
            </td>

        </tr>
        """

    if not history_html:

        history_html = """
        <tr>

            <td colspan="5">
                No analysis history yet.
            </td>

        </tr>
        """

    return f"""
<!DOCTYPE html>

<html>

<head>

<title>
Analysis History
</title>

<style>

* {{
    box-sizing: border-box;
}}

body {{

    font-family:
        Arial,
        Helvetica,
        sans-serif;

    background:
        linear-gradient(
            135deg,
            #eef2ff,
            #f8fafc
        );

    min-height: 100vh;

    padding: 40px 20px;

}}

.container {{

    max-width: 1000px;

    margin: auto;

    background: white;

    padding: 30px;

    border-radius: 20px;

    box-shadow:
        0 10px 30px
        rgba(15,23,42,0.08);

}}

h1 {{

    color: #1e3a8a;

    margin-bottom: 25px;

}}

.table-container {{

    overflow-x: auto;

}}

table {{

    width: 100%;

    border-collapse: collapse;

}}

th,
td {{

    padding: 14px;

    border-bottom:
        1px solid #e2e8f0;

    text-align: left;

}}

th {{

    background: #eef2ff;

    color: #1e3a8a;

}}

td {{

    color: #475569;

}}

.back {{

    display: inline-block;

    margin-top: 25px;

    padding: 13px 22px;

    background:
        linear-gradient(
            135deg,
            #2563eb,
            #4f46e5
        );

    color: white;

    text-decoration: none;

    border-radius: 10px;

    font-weight: bold;

}}

</style>

</head>


<body>

<div class="container">

<h1>
📊 Analysis History
</h1>


<div class="table-container">

<table>

<tr>

<th>
Resume
</th>

<th>
Overall
</th>

<th>
Skills
</th>

<th>
NLP
</th>

<th>
Date
</th>

</tr>


{history_html}


</table>

</div>


<a
    href="/"
    class="back"
>

← Analyze Resume

</a>


</div>

</body>

</html>
"""


# ==========================================
# ANALYZE RESUME
# ==========================================

@app.route(
    "/analyze",
    methods=["POST"]
)
def analyze():


    # ======================================
    # 1. GET RESUME
    # ======================================

    if "resume" not in request.files:

        return "No resume uploaded."


    file = request.files["resume"]


    if file.filename == "":

        return "Please select a resume."


    if not file.filename.lower().endswith(".pdf"):

        return "Please upload a PDF resume only."


    filename = secure_filename(
        file.filename
    )


    file_path = os.path.join(

        app.config["UPLOAD_FOLDER"],

        filename

    )


    file.save(
        file_path
    )


    # ======================================
    # 2. GET JOB DESCRIPTION
    # ======================================

    job_description = request.form.get(
        "job_description",
        ""
    ).strip()


    if not job_description:

        return "Please enter a job description."


    # ======================================
    # 3. EXTRACT RESUME TEXT
    # ======================================

    resume_text = extract_text_from_pdf(
        file_path
    )


    if not resume_text:

        return """
        <h1>
        Resume Text Could Not Be Extracted ❌
        </h1>

        <p>
        Please upload a text-based PDF resume.
        </p>
        """


    # ======================================
    # 4. EXTRACT SKILLS
    # ======================================

    resume_skills = extract_skills(
        resume_text
    )


    job_skills = extract_skills(
        job_description
    )


    # ======================================
    # 5. TECHNICAL SKILL MATCH
    # ======================================

    skill_result = calculate_match(

        resume_skills,

        job_skills

    )


    skill_score = skill_result[
        "score"
    ]


    matched_skills = skill_result[
        "matched_skills"
    ]


    missing_skills = skill_result[
        "missing_skills"
    ]


    # ======================================
    # 6. SEMANTIC NLP SCORE
    # ======================================

    nlp_score = calculate_text_similarity(

        resume_text,

        job_description

    )


    # ======================================
    # 7. OVERALL AI SCORE
    # ======================================

    overall_score = calculate_overall_score(

        skill_score,

        nlp_score

    )


    # ======================================
    # 8. SAVE ANALYSIS TO DATABASE
    # ======================================

    save_analysis(

        resume_name=filename,

        overall_score=overall_score,

        skill_score=skill_score,

        nlp_score=nlp_score,

        matched_skills=matched_skills,

        missing_skills=missing_skills

    )


    # ======================================
    # 9. MATCHED SKILLS HTML
    # ======================================

    if matched_skills:

        matched_html = ""

        for skill in matched_skills:

            matched_html += f"""

            <div class="skill matched">

                <span class="skill-icon">
                    ✓
                </span>

                <span>
                    {skill.title()}
                </span>

            </div>

            """

    else:

        matched_html = """

        <div class="empty">

            No matching skills found.

        </div>

        """


    # ======================================
    # 10. MISSING SKILLS HTML
    # ======================================

    if missing_skills:

        missing_html = ""

        for skill in missing_skills:

            missing_html += f"""

            <div class="skill missing">

                <span class="skill-icon">
                    ✗
                </span>

                <span>
                    {skill.title()}
                </span>

            </div>

            """

    else:

        missing_html = """

        <div class="empty">

            No missing skills detected.

        </div>

        """


    # ======================================
    # 11. RECOMMENDATIONS
    # ======================================

    recommendations = {

        "docker":
            "Learn Docker containers, images and basic deployment.",

        "machine learning":
            "Learn ML fundamentals, regression, classification and model evaluation.",

        "rest api":
            "Learn REST API concepts, HTTP methods and JSON.",

        "mysql":
            "Practice MySQL queries, joins and database design.",

        "sql":
            "Improve SQL queries, joins and database concepts.",

        "git":
            "Practice Git commands, branching and version control.",

        "github":
            "Learn GitHub repositories, branches and pull requests.",

        "pandas":
            "Practice Pandas for data cleaning and analysis.",

        "numpy":
            "Learn NumPy arrays and numerical operations.",

        "python":
            "Strengthen Python programming and problem-solving.",

        "java":
            "Practice Java OOP and core programming concepts.",

        "flask":
            "Learn Flask routing, APIs and backend development.",

        "javascript":
            "Strengthen JavaScript fundamentals and DOM manipulation.",

        "react":
            "Learn React components, props, state and hooks.",

        "django":
            "Learn Django models, views, URLs and REST APIs.",

        "mongodb":
            "Learn MongoDB collections, documents and CRUD operations.",

        "power bi":
            "Practice Power BI dashboards, data modeling and DAX.",

        "tableau":
            "Learn Tableau dashboards, charts and data visualization.",

        "c++":
            "Practice C++ programming, OOP and data structures.",

        "html":
            "Strengthen HTML structure, forms and semantic elements.",

        "css":
            "Practice CSS layouts, Flexbox, Grid and responsive design."

    }


    recommendations_html = ""


    for skill in missing_skills:

        if skill in recommendations:

            recommendations_html += f"""

            <div class="recommendation">

                <div class="recommendation-title">

                    📌 {skill.title()}

                </div>

                <div class="recommendation-text">

                    {recommendations[skill]}

                </div>

            </div>

            """


    if not recommendations_html:

        recommendations_html = """

        <div class="empty">

            🎉 No specific learning recommendations.

        </div>

        """


    # ======================================
    # 12. RESUME SKILLS
    # ======================================

    if resume_skills:

        resume_skills_html = ""

        for skill in resume_skills:

            resume_skills_html += f"""

            <span class="resume-skill">

                {skill.title()}

            </span>

            """

    else:

        resume_skills_html = """

        <div class="empty">

            No technical skills detected.

        </div>

        """


    # ======================================
    # 13. SCORE MESSAGE
    # ======================================

    if overall_score >= 80:

        score_message = "Strong overall match"

    elif overall_score >= 60:

        score_message = "Good overall match"

    elif overall_score >= 40:

        score_message = "Moderate overall match"

    else:

        score_message = "Low overall match"


    # ======================================
    # 14. RESULT PAGE
    # ======================================

    return f"""

<!DOCTYPE html>

<html lang="en">

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>
AI Resume Analysis
</title>


<style>

* {{

    box-sizing: border-box;

    margin: 0;

    padding: 0;

}}


body {{

    font-family:
        Arial,
        Helvetica,
        sans-serif;

    background:
        linear-gradient(
            135deg,
            #eef2ff,
            #f8fafc
        );

    min-height: 100vh;

    padding: 45px 20px;

    color: #1e293b;

}}


.container {{

    max-width: 1000px;

    margin: auto;

}}


.header {{

    text-align: center;

    margin-bottom: 35px;

}}


.header h1 {{

    font-size: 42px;

    color: #1e3a8a;

    margin-bottom: 10px;

}}


.header p {{

    color: #64748b;

    font-size: 17px;

}}


.card {{

    background: white;

    padding: 30px;

    border-radius: 20px;

    margin-bottom: 25px;

    box-shadow:
        0 10px 30px
        rgba(15,23,42,0.08);

    border: 1px solid #e2e8f0;

}}


h2 {{

    color: #1e293b;

    margin-bottom: 22px;

}}


/* SCORE */

.score-card {{

    text-align: center;

}}


.score-circle {{

    width: 190px;

    height: 190px;

    margin: 15px auto 20px;

    border-radius: 50%;

    background:
        linear-gradient(
            135deg,
            #2563eb,
            #4f46e5
        );

    display: flex;

    align-items: center;

    justify-content: center;

}}


.score {{

    font-size: 44px;

    font-weight: 800;

    color: white;

}}


.score-message {{

    color: #2563eb;

    font-weight: bold;

}}


/* METRICS */

.metrics {{

    display: grid;

    grid-template-columns:
        repeat(2,1fr);

    gap: 18px;

}}


.metric {{

    background: #f8fafc;

    padding: 22px;

    border-radius: 15px;

    text-align: center;

}}


.metric-value {{

    font-size: 30px;

    font-weight: 800;

    color: #2563eb;

}}


.metric-label {{

    color: #64748b;

    margin-top: 7px;

}}


/* SKILLS */

.skills-grid {{

    display: grid;

    grid-template-columns:
        repeat(2,1fr);

    gap: 12px;

}}


.skill {{

    padding: 14px 16px;

    border-radius: 12px;

    font-weight: bold;

    display: flex;

    gap: 10px;

}}


.matched {{

    background: #dcfce7;

    color: #166534;

}}


.missing {{

    background: #fee2e2;

    color: #991b1b;

}}


/* RECOMMENDATIONS */

.recommendations {{

    display: grid;

    gap: 14px;

}}


.recommendation {{

    background: #f8fafc;

    border-left:
        5px solid #2563eb;

    padding: 18px;

    border-radius: 12px;

}}


.recommendation-title {{

    font-weight: bold;

    color: #1e3a8a;

    margin-bottom: 7px;

}}


.recommendation-text {{

    color: #64748b;

    line-height: 1.5;

}}


/* RESUME SKILLS */

.resume-skills {{

    display: flex;

    flex-wrap: wrap;

    gap: 12px;

}}


.resume-skill {{

    background: #e0e7ff;

    color: #3730a3;

    padding: 10px 16px;

    border-radius: 25px;

    font-weight: bold;

}}


/* EMPTY */

.empty {{

    padding: 16px;

    background: #f1f5f9;

    border-radius: 12px;

    color: #64748b;

}}


/* BUTTON */

.buttons {{

    text-align: center;

    margin-top: 30px;

}}


.back-button {{

    display: inline-block;

    padding: 15px 28px;

    background:
        linear-gradient(
            135deg,
            #2563eb,
            #4f46e5
        );

    color: white;

    text-decoration: none;

    border-radius: 12px;

    font-weight: bold;

}}


.history-button {{

    display: inline-block;

    margin-left: 10px;

    padding: 15px 28px;

    background: #0f172a;

    color: white;

    text-decoration: none;

    border-radius: 12px;

    font-weight: bold;

}}


/* MOBILE */

@media(max-width:700px) {{

    .skills-grid,
    .metrics {{

        grid-template-columns: 1fr;

    }}

    .history-button {{

        margin-left: 0;

        margin-top: 10px;

    }}

}}

</style>

</head>


<body>

<div class="container">


<div class="header">

<h1>
🤖 AI Resume Analysis
</h1>

<p>
Resume vs Job Description Intelligence
</p>

</div>


<!-- SCORE -->

<div class="card score-card">

<h2>
🎯 Overall AI Match Score
</h2>

<div class="score-circle">

<div class="score">

{overall_score}%

</div>

</div>

<div class="score-message">

{score_message}

</div>

</div>


<!-- METRICS -->

<div class="card">

<h2>
🧠 AI Analysis Metrics
</h2>

<div class="metrics">

<div class="metric">

<div class="metric-value">

{skill_score}%

</div>

<div class="metric-label">

Technical Skill Match

</div>

</div>


<div class="metric">

<div class="metric-value">

{nlp_score}%

</div>

<div class="metric-label">

Semantic AI Similarity

</div>

</div>

</div>

</div>


<!-- MATCHED -->

<div class="card">

<h2>
✅ Matched Skills
</h2>

<div class="skills-grid">

{matched_html}

</div>

</div>


<!-- MISSING -->

<div class="card">

<h2>
📚 Missing Skills
</h2>

<div class="skills-grid">

{missing_html}

</div>

</div>


<!-- RECOMMENDATIONS -->

<div class="card">

<h2>
💡 Recommended Learning
</h2>

<div class="recommendations">

{recommendations_html}

</div>

</div>


<!-- RESUME SKILLS -->

<div class="card">

<h2>
🧠 Skills Detected in Resume
</h2>

<div class="resume-skills">

{resume_skills_html}

</div>

</div>


<!-- BUTTONS -->

<div class="buttons">

<a
href="/"
class="back-button"
>
← Analyze Another Resume
</a>


<a
href="/history"
class="history-button"
>
📊 Analysis History
</a>

</div>


</div>

</body>

</html>

"""


# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == "__main__":

    app.run(
        debug=True
    )