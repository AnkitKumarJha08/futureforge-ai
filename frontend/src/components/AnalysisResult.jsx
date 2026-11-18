function AnalysisResult({ result }) {
  if (!result) return null;

  return (
    <div className="analysis-container">

      <div className="score-card">
        <h2>ATS Score</h2>
        <div className="score-circle">
          {result.score}
        </div>
      </div>

      <div className="skills-card">
        <h2>Skills Found</h2>
        <div className="badge-container">
          {result.skills.map((skill, index) => (
            <span className="badge success" key={index}>
              {skill}
            </span>
          ))}
        </div>
      </div>

      <div className="missing-card">
        <h2>Missing Skills</h2>
        <div className="badge-container">
          {result.missing_skills.map((skill, index) => (
            <span className="badge danger" key={index}>
              {skill}
            </span>
          ))}
        </div>
      </div>

      <div className="suggestion-card">
        <h2>Smart Suggestions</h2>

        <ul>
          {result.suggestions.map((item, index) => (
            <li key={index}>{item}</li>
          ))}
        </ul>

      </div>

    </div>
  );
}

export default AnalysisResult;