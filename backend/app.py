import os, re, sqlite3, secrets, time, bcrypt
from pathlib import Path
from functools import wraps
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from services.ats_engine import analyze_resume
from services.career_engine import recommend_careers, skills_gap, CAREERS
from services.roadmap_engine import create_roadmap
from services.skill_extractor import extract_skills

BASE_DIR=Path(__file__).resolve().parent
DB_PATH=Path(os.getenv('FUTUREFORGE_DB', str(BASE_DIR/'futureforge.db')))
UPLOAD_DIR=BASE_DIR/'uploads'; UPLOAD_DIR.mkdir(exist_ok=True)
app=Flask(__name__)
app.config['JWT_SECRET_KEY']=os.getenv('JWT_SECRET_KEY') or 'dev-only-change-this-secret-before-deployment'
app.config['JWT_ACCESS_TOKEN_EXPIRES']=3600
app.config['MAX_CONTENT_LENGTH']=8*1024*1024
CORS(app, resources={r'/*': {'origins': os.getenv('CORS_ORIGINS','http://localhost:5173,http://127.0.0.1:5173').split(',')}})
jwt=JWTManager(app)

def connect():
    conn=sqlite3.connect(DB_PATH, timeout=15); conn.row_factory=sqlite3.Row; return conn

def init_db():
    with connect() as c:
        c.executescript('''CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,email TEXT UNIQUE NOT NULL,password_hash TEXT NOT NULL,role TEXT NOT NULL DEFAULT 'user',created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS resumes(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,filename TEXT NOT NULL,score INTEGER NOT NULL,analysis_json TEXT NOT NULL,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(user_id) REFERENCES users(id));
        CREATE TABLE IF NOT EXISTS assessments(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,career TEXT NOT NULL,payload_json TEXT NOT NULL,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);''')
        # Migrate the earlier prototype schema in place, without deleting user records.
        columns={r['name'] for r in c.execute('PRAGMA table_info(users)').fetchall()}
        if 'password_hash' not in columns:
            c.execute('ALTER TABLE users ADD COLUMN password_hash TEXT')
            if 'password' in columns:
                for old in c.execute('SELECT id,password FROM users WHERE password_hash IS NULL').fetchall():
                    raw=old['password']
                    if isinstance(raw,bytes): raw=raw.decode('utf-8','ignore')
                    if raw:
                        # Legacy bcrypt hashes are accepted for login after migration.
                        c.execute('UPDATE users SET password_hash=? WHERE id=?',(str(raw),old['id']))
        if 'role' not in columns: c.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'")
        if 'created_at' not in columns:
            c.execute('ALTER TABLE users ADD COLUMN created_at TEXT')
            c.execute('UPDATE users SET created_at=CURRENT_TIMESTAMP WHERE created_at IS NULL')
        row=c.execute('SELECT id FROM users WHERE email=?',('admin@futureforge.com',)).fetchone()
        if not row:
            c.execute('INSERT INTO users(name,email,password_hash,role) VALUES(?,?,?,?)',('FutureForge Admin','admin@futureforge.com',generate_password_hash(os.getenv('ADMIN_PASSWORD','admin123')),'admin'))
init_db()

def password_matches(stored, candidate):
    if not stored: return False
    try:
        if str(stored).startswith(('pbkdf2:','scrypt:')): return check_password_hash(stored,candidate)
        return bcrypt.checkpw(candidate.encode('utf-8'),str(stored).encode('utf-8'))
    except (ValueError, TypeError): return False
def fail(message,status=400): return jsonify({'status':False,'message':message}),status
def payload(): return request.get_json(silent=True) or {}
def current_user():
    ident=get_jwt_identity()
    try: uid=int(ident)
    except (ValueError,TypeError): return None
    with connect() as c: row=c.execute('SELECT id,name,email,role FROM users WHERE id=?',(uid,)).fetchone()
    return dict(row) if row else None
def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapped(*args,**kwargs):
        user=current_user()
        if not user or user['role']!='admin': return fail('Admin authorization required',403)
        g.user=user
        return fn(*args,**kwargs)
    return wrapped
@app.get('/health')
def health(): return jsonify({'status':True,'service':'FutureForge AI API','database':'sqlite','version':'1.0'})
@app.post('/register')
def register():
    d=payload(); name=str(d.get('name','')).strip(); email=str(d.get('email','')).strip().lower(); password=d.get('password','')
    if not name or len(name)>100 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email): return fail('Enter a name and valid email address.')
    if not isinstance(password,str) or len(password)<8: return fail('Password must contain at least 8 characters.')
    try:
        with connect() as c: c.execute('INSERT INTO users(name,email,password_hash) VALUES(?,?,?)',(name,email,generate_password_hash(password)))
    except sqlite3.IntegrityError: return fail('An account with this email already exists.',409)
    return jsonify({'status':True,'message':'Registration successful. You can now log in.'}),201
@app.post('/login')
def login():
    d=payload(); email=str(d.get('email','')).strip().lower(); password=d.get('password','')
    with connect() as c: user=c.execute('SELECT * FROM users WHERE email=?',(email,)).fetchone()
    if not user or not isinstance(password,str) or not password_matches(user['password_hash'],password): return fail('Invalid email or password.',401)
    token=create_access_token(identity=str(user['id']),additional_claims={'role':user['role']})
    return jsonify({'status':True,'message':'Login successful','access_token':token,'token':token,'user':{'id':user['id'],'name':user['name'],'email':user['email'],'role':user['role']}})
@app.post('/admin/login')
def admin_login():
    d=payload(); email=str(d.get('email','')).strip().lower(); password=d.get('password','')
    with connect() as c: user=c.execute('SELECT * FROM users WHERE email=? AND role=?',(email,'admin')).fetchone()
    if not user or not isinstance(password,str) or not password_matches(user['password_hash'],password): return fail('Invalid admin credentials.',401)
    token=create_access_token(identity=str(user['id']),additional_claims={'role':'admin'})
    return jsonify({'status':True,'message':'Admin login successful','access_token':token,'token':token,'user':{'id':user['id'],'name':user['name'],'email':user['email'],'role':'admin'}})
@app.get('/me')
@jwt_required()
def me():
    u=current_user(); return (jsonify({'user':u}),200) if u else fail('Account not found.',404)
@app.get('/careers')
def careers(): return jsonify({'careers':list(CAREERS.keys())})
@app.post('/career/recommend')
@app.post('/career/recommendations')
def career_recommend():
    d=payload(); text=str(d.get('resume_text','')); interests=d.get('interests',[])
    if not isinstance(interests,list): return fail('interests must be a list.')
    results=recommend_careers(text,interests)
    if get_jwt_identity_safe():
        uid=int(get_jwt_identity_safe())
        with connect() as c: c.execute('INSERT INTO assessments(user_id,career,payload_json) VALUES(?,?,?)',(uid,results[0]['career'],__import__('json').dumps(d)))
    return jsonify({'recommendations':results,'top_match':results[0] if results else None})
def get_jwt_identity_safe():
    try: return get_jwt_identity()
    except Exception: return None
@app.post('/skills-gap')
def skills_gap_route():
    d=payload(); career=d.get('career'); skills=d.get('current_skills',[])
    if isinstance(skills,str): skills=[x.strip() for x in skills.split(',') if x.strip()]
    if not isinstance(skills,list): return fail('current_skills must be a list or comma-separated string.')
    try: return jsonify(skills_gap(str(career),skills))
    except ValueError as e: return fail(str(e))
@app.route('/roadmap',methods=['GET','POST'])
def roadmap():
    d=payload() if request.method=='POST' else request.args; career=d.get('career','Software Engineer')
    try: return jsonify(create_roadmap(str(career)))
    except ValueError as e: return fail(str(e))
@app.post('/resume/analyze')
@app.post('/resume/upload')
@jwt_required()
def resume_upload():
    file=request.files.get('resume') or request.files.get('file')
    if not file or not file.filename: return fail('Choose a PDF or text resume to upload.')
    filename=secure_filename(file.filename)
    if Path(filename).suffix.lower() not in {'.pdf','.txt'}: return fail('Only PDF and TXT resumes are supported.')
    dest=UPLOAD_DIR/f'{int(get_jwt_identity())}_{secrets.token_hex(5)}_{filename}'; file.save(dest)
    try:
        if dest.suffix.lower()=='.pdf':
            try:
                import fitz
                with fitz.open(dest) as doc: text='\n'.join(p.get_text() for p in doc)
            except ImportError: return fail('PDF parsing dependency is missing. Install backend requirements.',500)
        else: text=dest.read_text(encoding='utf-8',errors='ignore')
        if not text.strip(): return fail('No readable text found. For scanned PDFs, run OCR first.')
        result=analyze_resume(text); result['filename']=filename
        with connect() as c: c.execute('INSERT INTO resumes(user_id,filename,score,analysis_json) VALUES(?,?,?,?)',(int(get_jwt_identity()),filename,result['score'],__import__('json').dumps(result)))
        return jsonify(result)
    finally:
        try: dest.unlink()
        except OSError: pass
@app.get('/resume/history')
@jwt_required()
def resume_history():
    with connect() as c: rows=c.execute('SELECT id,filename,score,created_at FROM resumes WHERE user_id=? ORDER BY id DESC',(int(get_jwt_identity()),)).fetchall()
    return jsonify({'resumes':[dict(x) for x in rows]})
@app.post('/interview/questions')
def interview_questions():
    d=payload(); role=str(d.get('role','Software Engineer')).strip(); skills=d.get('skills',[])
    if isinstance(skills,str): skills=[s.strip() for s in skills.split(',') if s.strip()]
    questions=[f'Explain the core responsibilities of a {role}.','Describe a project relevant to this role and the trade-offs you made.','How do you debug a difficult production issue?','How do you test your work and prevent regressions?']
    questions += [f'Explain {s} and describe a practical use case.' for s in skills[:6]]
    questions += ['Tell me about a time you received critical feedback.','How would you approach learning an unfamiliar technology?']
    return jsonify({'role':role,'questions':questions})
@app.get('/jobs/search')
@jwt_required()
def jobs_search():
    # Uses Adzuna when credentials are configured; never fabricates live listings.
    import urllib.parse, urllib.request, json
    query=request.args.get('q','software developer').strip()[:120]; location=request.args.get('location','India').strip()[:80]
    app_id=os.getenv('ADZUNA_APP_ID'); app_key=os.getenv('ADZUNA_APP_KEY')
    if not app_id or not app_key: return jsonify({'jobs':[],'configured':False,'message':'Job search requires ADZUNA_APP_ID and ADZUNA_APP_KEY environment variables. Add your Adzuna API credentials to enable live listings.'})
    params=urllib.parse.urlencode({'app_id':app_id,'app_key':app_key,'what':query,'where':location,'results_per_page':20,'content-type':'application/json'})
    url='https://api.adzuna.com/v1/api/jobs/in/search/1?'+params
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'FutureForgeAI/1.0'})
        with urllib.request.urlopen(req,timeout=10) as r: data=json.loads(r.read().decode())
        jobs=[{'id':str(x.get('id','')),'title':x.get('title'),'company':(x.get('company') or {}).get('display_name'),'location':(x.get('location') or {}).get('display_name'),'description':(x.get('description') or '')[:400],'url':x.get('redirect_url'),'created':x.get('created')} for x in data.get('results',[])]
        return jsonify({'jobs':jobs,'configured':True,'count':len(jobs)})
    except Exception: return fail('Live job provider could not be reached. Check API credentials and try again.',502)
@app.get('/admin/users')
@admin_required
def admin_users():
    with connect() as c: rows=c.execute("SELECT id,name,email,role,created_at FROM users ORDER BY id DESC").fetchall()
    return jsonify([dict(x) for x in rows])
@app.get('/admin/analytics')
@admin_required
def admin_analytics():
    with connect() as c:
        users=c.execute("SELECT COUNT(*) n FROM users WHERE role='user'").fetchone()['n']; resumes=c.execute('SELECT COUNT(*) n FROM resumes').fetchone()['n']; assessments=c.execute('SELECT COUNT(*) n FROM assessments').fetchone()['n']; recent=[dict(x) for x in c.execute('SELECT id,filename,score,created_at FROM resumes ORDER BY id DESC LIMIT 10').fetchall()]
    return jsonify({'users':users,'resumes_analyzed':resumes,'career_assessments':assessments,'recent_resumes':recent})
@app.errorhandler(413)
def too_large(_): return fail('File is too large. Maximum upload size is 8 MB.',413)
@app.errorhandler(404)
def not_found(_): return fail('API endpoint not found.',404)
if __name__=='__main__': app.run(host='127.0.0.1',port=int(os.getenv('PORT','5000')),debug=os.getenv('FLASK_DEBUG')=='1')
