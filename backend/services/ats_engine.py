import re
from services.skill_extractor import extract_skills
def analyze_resume(text):
    text=text or ""; lower=text.lower(); skills=extract_skills(text)
    sections={"Contact information": bool(re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+",text)),"Professional summary": any(x in lower for x in ["summary","objective","profile"]),"Education": "education" in lower or "university" in lower or "college" in lower,"Experience": any(x in lower for x in ["experience","employment","internship"]),"Projects": "project" in lower,"Skills": "skill" in lower or bool(skills),"Certifications": any(x in lower for x in ["certification","certified"]) }
    score=min(100, round((sum(sections.values())/len(sections))*70 + min(len(skills),10)*3))
    missing=[name for name,ok in sections.items() if not ok]
    suggestions=[f"Add a clear {x.lower()} section." for x in missing]
    if not re.search(r"\b(action|built|developed|implemented|improved|created|managed|led)\b",lower): suggestions.append("Use action verbs to describe measurable outcomes.")
    if not skills: suggestions.append("Include relevant technical skills using terms from target job descriptions.")
    return {"score":score,"skills":skills,"sections":sections,"missing_sections":missing,"suggestions":suggestions,"word_count":len(text.split())}
