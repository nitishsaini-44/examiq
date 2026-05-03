const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function uploadPapers(files) {
  const formData = new FormData();
  files.forEach(f => formData.append('files', f));
  const res = await fetch(`${API_BASE}/api/upload/papers`, { method: 'POST', body: formData });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function uploadSyllabus(file) {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE}/api/upload/syllabus`, { method: 'POST', body: formData });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function runAnalysis(params = {}) {
  const res = await fetch(`${API_BASE}/api/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ exam_days: 30, hours_per_day: 6, subject: 'General', ...params }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getResults() {
  const res = await fetch(`${API_BASE}/api/results`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getDashboard() {
  const res = await fetch(`${API_BASE}/api/dashboard`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getUploadStatus() {
  const res = await fetch(`${API_BASE}/api/upload/status`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
