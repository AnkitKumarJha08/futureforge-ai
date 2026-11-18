import fitz  # PyMuPDF

SKILLS = [
    "python",
    "java",
    "c++",
    "javascript",
    "react",
    "node",
    "sql",
    "mongodb",
    "html",
    "css",
    "flask",
    "django",
    "git",
    "docker",
    "aws"
]

def extract_text(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""

    for page in doc:
        text += page.get_text()

    return text.lower()


def analyze_resume(text):
    found_skills = []

    for skill in SKILLS:
        if skill in text:
            found_skills.append(skill.title())

    score = min(len(found_skills) * 7, 100)

    missing = [
        skill.title()
        for skill in SKILLS
        if skill.title() not in found_skills
    ]

    suggestions = []

    if score < 50:
        suggestions.append("Add more technical skills.")
        suggestions.append("Include projects.")
        suggestions.append("Mention certifications.")

    return {
        "score": score,
        "skills": found_skills,
        "missing_skills": missing[:5],
        "suggestions": suggestions
    }