from services.skill_extractor import extract_skills
CAREERS={"Software Engineer":["Python","JavaScript","React","SQL","Git","REST API","Docker"],"Data Analyst":["SQL","Python","Excel","Pandas","Power BI","Tableau","Communication"],"Data Scientist":["Python","SQL","Pandas","NumPy","Machine Learning","Statistics"],"Full Stack Developer":["HTML","CSS","JavaScript","React","Node.js","SQL","Git","REST API"],"Cloud Engineer":["Linux","AWS","Docker","Kubernetes","Python","Networking"],"UI/UX Designer":["Figma","Communication","User Research","Prototyping"]}
def recommend_careers(text='', interests=None):
    found=set(extract_skills(text or '')+[str(x) for x in (interests or [])]); rows=[]
    for career,required in CAREERS.items():
        matched=[x for x in required if x.lower() in {s.lower() for s in found}]
        rows.append({"career":career,"match_score":round(100*len(matched)/len(required)),"matched_skills":matched,"missing_skills":[x for x in required if x not in matched],"required_skills":required})
    return sorted(rows,key=lambda x:x['match_score'],reverse=True)
def skills_gap(career, current_skills):
    required=CAREERS.get(career)
    if not required: raise ValueError('Unsupported career. Choose a listed career.')
    current={str(x).strip().lower() for x in current_skills}; missing=[s for s in required if s.lower() not in current]
    return {"career":career,"required_skills":required,"current_skills":[s for s in required if s.lower() in current],"missing_skills":missing,"completion_score":round(100*(len(required)-len(missing))/len(required))}
