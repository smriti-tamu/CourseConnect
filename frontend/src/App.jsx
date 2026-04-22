import { useState } from "react";

const API_BASE = "http://127.0.0.1:8000";

const sampleQueries = [
  "deep learning for computer vision",
  "security in distributed systems",
  "machine learning for large datasets",
];

export default function App() {
  const [query, setQuery] = useState(sampleQueries[0]);
  const [level, setLevel] = useState("all");
  const [expandedCourses, setExpandedCourses] = useState({});
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function runSearch(nextQuery) {
    const text = nextQuery ?? query;
    if (!text.trim()) return;

    setLoading(true);
    setError("");

    try {
      const params = new URLSearchParams({
        q: text,
        top_k: "5",
      });
      if (level !== "all") {
        params.set("level", level);
      }
      const response = await fetch(`${API_BASE}/search?${params.toString()}`);
      if (!response.ok) {
        throw new Error("Search request failed.");
      }
      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError(err.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  function toggleCourse(courseId) {
    setExpandedCourses((current) => ({
      ...current,
      [courseId]: !current[courseId],
    }));
  }

  return (
    <main className="page-shell">
      <section className="hero">
        <p className="eyebrow">Texas A&M Cross-Department Course Discovery</p>
        <h1>CourseConnect</h1>
        <p className="hero-copy">
          Search Texas A&amp;M undergraduate and graduate courses with natural
          language instead of relying only on catalog keywords.
        </p>

        <div className="search-card">
          <label htmlFor="query" className="label">
            Describe your research interests
          </label>
          <div className="search-row">
            <input
              id="query"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Try: deep learning for healthcare"
            />
            <select
              value={level}
              onChange={(e) => setLevel(e.target.value)}
              aria-label="Course level filter"
            >
              <option value="all">All courses</option>
              <option value="undergraduate">Undergraduate</option>
              <option value="graduate">Graduate</option>
            </select>
            <button onClick={() => runSearch()}>Search</button>
          </div>

          <div className="chips">
            {sampleQueries.map((item) => (
              <button
                key={item}
                className="chip"
                onClick={() => {
                  setQuery(item);
                  runSearch(item);
                }}
              >
                {item}
              </button>
            ))}
          </div>
        </div>
      </section>

      <section className="results-section">
        <div className="results-header">
          <h2>Ranked Results</h2>
          {loading && <span className="status">Searching...</span>}
        </div>

        {error && <div className="error-box">{error}</div>}

        {!loading && results.length === 0 && (
          <div className="empty-state">
            Search to see matching courses.
          </div>
        )}

        <div className="results-grid">
          {results.map((course) => (
            <article key={course.id} className="course-card">
              <div className="course-summary">
                <div className="course-topline">
                  <span className="course-code">{course.code}</span>
                  <span className="score-pill">
                    Score {course.score.toFixed(3)}
                  </span>
                </div>
                <h3>{course.title}</h3>
                <div className="muted course-summary-meta">
                  <div>
                    <strong>Level:</strong> {course.level || "unknown"}
                  </div>
                  <div>
                    <strong>Department:</strong> {course.department || "unknown"}
                  </div>
                </div>
              </div>

              {expandedCourses[course.id] && (
                <div className="course-details">
                  <p>{course.description}</p>
                  {course.topics && (
                    <p className="muted">
                      <strong>Topics:</strong> {course.topics}
                    </p>
                  )}
                  {course.prerequisites && (
                    <p className="muted">
                      <strong>Prerequisites:</strong> {course.prerequisites}
                    </p>
                  )}
                  <p className="match-reason">
                    <strong>Why it matched:</strong> {course.match_reason}
                  </p>
                </div>
              )}

              <button
                className="course-toggle"
                onClick={() => toggleCourse(course.id)}
                aria-expanded={Boolean(expandedCourses[course.id])}
                aria-label={expandedCourses[course.id] ? "Collapse details" : "Expand details"}
              >
                {expandedCourses[course.id] ? "Hide details" : "Details"}
              </button>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
