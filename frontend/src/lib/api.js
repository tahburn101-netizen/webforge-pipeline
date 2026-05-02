import axios from "axios";

export const API_BASE = (process.env.REACT_APP_BACKEND_URL || "").replace(/\/$/, "");
export const API = `${API_BASE}/api`;

export const api = axios.create({ baseURL: API });

export async function createJob(payload) {
  const { data } = await api.post("/jobs", payload);
  return data;
}

export async function getJob(id) {
  const { data } = await api.get(`/jobs/${id}`);
  return data;
}

export async function listJobs() {
  const { data } = await api.get("/jobs");
  return data;
}

export async function uploadVideo(jobId, file, onProgress) {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post(`/jobs/${jobId}/upload-video`, form, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (e) => {
      if (!onProgress || !e.total) return;
      onProgress(Math.round((e.loaded * 100) / e.total));
    },
  });
  return data;
}

export function artifactUrl(jobId, name) {
  return `${API}/jobs/${jobId}/artifact/${name}`;
}

export function eventsUrl(jobId) {
  return `${API}/jobs/${jobId}/events`;
}

export async function deleteJob(id) {
  await api.delete(`/jobs/${id}`);
}
