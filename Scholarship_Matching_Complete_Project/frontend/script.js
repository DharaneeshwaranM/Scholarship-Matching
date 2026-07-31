const API_BASE = ""; // same origin (Flask serves both API and frontend)

const form = document.getElementById("profile-form");
const loading = document.getElementById("loading");
const resultsSection = document.getElementById("results-section");
const resultsList = document.getElementById("results-list");
const resultsSummary = document.getElementById("results-summary");
const excludedList = document.getElementById("excluded-list");
const excludedSummary = document.getElementById("excluded-summary");
const downloadBtn = document.getElementById("download-btn");
const browseBtn = document.getElementById("browse-btn");
const allSchemesList = document.getElementById("all-schemes-list");

let lastStudent = null;
let lastResults = null;

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const student = {
    name: document.getElementById("name").value || "Student",
    income: parseFloat(document.getElementById("income").value),
    category: document.getElementById("category").value,
    tenth_pct: document.getElementById("tenth_pct").value
      ? parseFloat(document.getElementById("tenth_pct").value)
      : null,
    twelfth_pct: parseFloat(document.getElementById("twelfth_pct").value),
    state: document.getElementById("state").value,
    course: document.getElementById("course").value,
    gender: document.getElementById("gender").value,
  };

  loading.classList.remove("hidden");
  resultsSection.classList.add("hidden");

  try {
    const res = await fetch(`${API_BASE}/api/match`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(student),
    });
    const data = await res.json();

    if (!res.ok) {
      alert(data.error || "Something went wrong.");
      return;
    }

    lastStudent = student;
    lastResults = data.results;

    renderResults(data);
    resultsSection.classList.remove("hidden");
    resultsSection.scrollIntoView({ behavior: "smooth" });
  } catch (err) {
    alert("Could not reach the server. Is the backend running?");
    console.error(err);
  } finally {
    loading.classList.add("hidden");
  }
});

function renderResults(data) {
  resultsSummary.textContent =
    `${data.eligible_count} matching scholarship(s) found out of ${data.eligible_count + data.excluded_count} total schemes.`;

  resultsList.innerHTML = "";
  if (data.results.length === 0) {
    resultsList.innerHTML = "<p>No eligible scholarships found for this profile yet — try browsing all schemes below.</p>";
  }
  data.results.forEach((item) => {
    const s = item.scheme;
    const div = document.createElement("div");
    div.className = "scheme-card";
    div.innerHTML = `
      <div class="rank-badge">${item.rank}</div>
      <div class="scheme-main">
        <h3>${s.scheme_name}</h3>
        <div class="scheme-meta">Provider: ${s.provider}</div>
        <div class="scheme-meta">Deadline: ${s.deadline || "—"}</div>
        <div class="scheme-meta">Documents: ${s.documents_required || "—"}</div>
      </div>
      <div class="score-pill">Score ${item.match_score}</div>
    `;
    resultsList.appendChild(div);
  });

  excludedSummary.textContent = `Show schemes you're not eligible for (${data.excluded_count}) and why`;
  excludedList.innerHTML = "";
  data.excluded.forEach((ex) => {
    const div = document.createElement("div");
    div.className = "excluded-item";
    div.innerHTML = `
      <h4>${ex.scheme_name}</h4>
      <ul>${ex.reasons.map((r) => `<li>${r}</li>`).join("")}</ul>
    `;
    excludedList.appendChild(div);
  });
}

downloadBtn.addEventListener("click", async () => {
  if (!lastStudent || !lastResults) {
    alert("Search for scholarships first.");
    return;
  }
  const res = await fetch(`${API_BASE}/api/summary`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ student: lastStudent, results: lastResults }),
  });
  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "scholarship_summary.txt";
  a.click();
  window.URL.revokeObjectURL(url);
});

browseBtn.addEventListener("click", async () => {
  const res = await fetch(`${API_BASE}/api/schemes`);
  const schemes = await res.json();
  let html = "<table><thead><tr><th>Scheme</th><th>Provider</th><th>Income Limit</th><th>Category</th><th>Min Marks</th><th>State</th><th>Deadline</th></tr></thead><tbody>";
  schemes.forEach((s) => {
    html += `<tr>
      <td>${s.scheme_name}</td>
      <td>${s.provider}</td>
      <td>${s.income_limit ? "₹" + Number(s.income_limit).toLocaleString() : "No limit"}</td>
      <td>${s.eligible_category}</td>
      <td>${s.min_marks || "—"}</td>
      <td>${s.state_applicable}</td>
      <td>${s.deadline || "—"}</td>
    </tr>`;
  });
  html += "</tbody></table>";
  allSchemesList.innerHTML = html;
});
