import { useState } from 'react';
import API from '../services/api';

export default function InterviewPrep() {
  const [role, setRole] = useState('Software Engineer');
  const [skills, setSkills] = useState('Python, React, SQL');
  const [questions, setQuestions] = useState([]);
  const [error, setError] = useState('');
  async function generate(e) {
    e.preventDefault(); setError('');
    try {
      const { data } = await API.post('/interview/questions', { role, skills });
      setQuestions(data.questions || []);
    } catch (err) { setError(err.response?.data?.message || 'Could not generate questions.'); }
  }
  return <section className="assessment-card"><h2>🎤 Interview Question Generator</h2><form onSubmit={generate}><label>Target role</label><input value={role} onChange={e => setRole(e.target.value)} required/><label>Skills (comma-separated)</label><input value={skills} onChange={e => setSkills(e.target.value)}/><button>Generate questions</button></form>{error && <p role="alert">{error}</p>}{questions.length > 0 && <ol>{questions.map((q, i) => <li key={`${i}-${q}`}>{q}</li>)}</ol>}</section>;
}
