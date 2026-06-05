import axios from "axios";
import type {
  Repository,
  IngestionJob,
  FileTreeNode,
  FileHistory,
  AskResponse,
  GraphData,
  Hotspot,
  RepositoryStats,
  TimelineEvent,
} from "./types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 60000,
  headers: { "Content-Type": "application/json" },
});

// ---- Repositories ----

export async function createRepository(data: {
  github_url: string;
  github_token?: string;
  include_issues: boolean;
  include_pr_comments: boolean;
  include_commit_diffs: boolean;
  include_docs: boolean;
}): Promise<{ repository_id: string; ingestion_job_id: string; status: string }> {
  const res = await api.post("/api/repositories", data);
  return res.data;
}

export async function listRepositories(): Promise<Repository[]> {
  const res = await api.get("/api/repositories");
  return res.data;
}

export async function getRepository(repoId: string): Promise<Repository> {
  const res = await api.get(`/api/repositories/${repoId}`);
  return res.data;
}

export async function deleteRepository(repoId: string): Promise<void> {
  await api.delete(`/api/repositories/${repoId}`);
}

export async function reindexRepository(repoId: string): Promise<{ ingestion_job_id: string }> {
  const res = await api.post(`/api/repositories/${repoId}/reindex`);
  return res.data;
}

// ---- Ingestion ----

export async function getIngestionStatus(repoId: string): Promise<IngestionJob> {
  const res = await api.get(`/api/repositories/${repoId}/ingestion`);
  return res.data;
}

// ---- Files ----

export async function getFileTree(repoId: string): Promise<FileTreeNode[]> {
  const res = await api.get(`/api/repositories/${repoId}/files`);
  return res.data;
}

export async function getFileContent(repoId: string, fileId: string): Promise<{ path: string; content: string; language: string }> {
  const res = await api.get(`/api/repositories/${repoId}/files/${fileId}/content`);
  return res.data;
}

export async function getFileHistory(repoId: string, fileId: string): Promise<FileHistory> {
  const res = await api.get(`/api/repositories/${repoId}/files/${fileId}/history`);
  return res.data;
}

// ---- Ask ----

export async function askQuestion(
  repoId: string,
  question: string,
  context?: {
    file_path?: string;
    start_line?: number;
    end_line?: number;
    selected_text?: string;
    symbol_name?: string;
  }
): Promise<AskResponse> {
  const res = await api.post(`/api/repositories/${repoId}/ask`, {
    question,
    context,
  });
  return res.data;
}

export async function getQuestionHistory(repoId: string) {
  const res = await api.get(`/api/repositories/${repoId}/questions`);
  return res.data;
}

// ---- Timeline ----

export async function getTimeline(
  repoId: string,
  filters: {
    file_path?: string;
    keyword?: string;
    start_date?: string;
    end_date?: string;
  } = {}
): Promise<{ events: TimelineEvent[]; total: number }> {
  const params = Object.fromEntries(
    Object.entries(filters).filter(([, v]) => v !== undefined && v !== "")
  );
  const res = await api.get(`/api/repositories/${repoId}/timeline`, { params });
  return res.data;
}

// ---- Graph ----

export async function getKnowledgeGraph(
  repoId: string,
  filters: { file_path?: string; relationship_types?: string; depth?: number } = {}
): Promise<GraphData> {
  const res = await api.get(`/api/repositories/${repoId}/graph`, { params: filters });
  return res.data;
}

// ---- Hotspots ----

export async function getHotspots(repoId: string): Promise<{ hotspots: Hotspot[] }> {
  const res = await api.get(`/api/repositories/${repoId}/hotspots`);
  return res.data;
}

export async function getStats(repoId: string): Promise<RepositoryStats> {
  const res = await api.get(`/api/repositories/${repoId}/stats`);
  return res.data;
}

// ---- Demo ----

export async function seedDemo(): Promise<{ repository_id: string; status: string }> {
  const res = await api.get("/api/demo/seed");
  return res.data;
}
