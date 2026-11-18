import re
SKILLS = ["Python","Java","JavaScript","TypeScript","C++","React","Node.js","SQL","PostgreSQL","MySQL","MongoDB","HTML","CSS","Flask","Django","FastAPI","Git","Docker","AWS","Azure","Machine Learning","Deep Learning","Pandas","NumPy","Power BI","Tableau","Figma","REST API","Linux","Kubernetes","Excel","Communication","Leadership"]
def extract_skills(text):
    source=(text or "").lower()
    found=[]
    for skill in SKILLS:
        pattern=r"(?<![a-z0-9+#])"+re.escape(skill.lower())+r"(?![a-z0-9+#])"
        if re.search(pattern, source): found.append(skill)
    return found
