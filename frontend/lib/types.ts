export interface Repository {
  id: string;
  owner: string;
  name: string;
  github_url: string;
  default_branch: string;
  status: "pending" | "ingesting" | "ready" | "failed";
  created_at: string;
  updated_at: string;
  stats?: RepositoryStats;
}

export interface RepositoryStats {
  total_files: number;
  total_commits: number;
  total_prs: number;
  total_issues: number;
  total_authors: number;
  oldest_commit: string | null;
  top_churn_files: ChurnFile[];
  top_authors: AuthorStat[];
  commits_over_time: CommitOverTime[];
}

export interface ChurnFile {
  path: string;
  churn_score: number;
  author_count: number;
}

export interface AuthorStat {
  name: string;
  commit_count: number;
}

export interface CommitOverTime {
  month: string;
  count: number;
}

export interface IngestionJob {
  id: string;
  repository_id: string;
  status: "queued" | "running" | "completed" | "failed";
  current_stage: string;
  progress_percent: number;
  logs: LogEntry[] | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface LogEntry {
  ts: string;
  stage: string;
  msg: string;
}

export interface FileTreeNode {
  name: string;
  path: string;
  type: "file" | "directory";
  language?: string;
  size_bytes?: number;
  churn_score?: number;
  children?: FileTreeNode[];
}

export interface FileHistory {
  file_id: string;
  file_path: string;
  commits: CommitSummary[];
  authors: { name: string; commits: number }[];
  pull_requests: PRSummary[];
  issues: IssueSummary[];
  timeline: TimelineEvent[];
  churn_score: number;
  first_seen: string | null;
  last_modified: string | null;
}

export interface CommitSummary {
  sha: string;
  message: string;
  author: string;
  date: string;
  github_url: string | null;
  status: string;
  additions: number;
  deletions: number;
}

export interface PRSummary {
  number: number;
  title: string;
  state: string;
  author: string;
  merged: boolean;
  date: string;
  github_url: string;
}

export interface IssueSummary {
  number: number;
  title: string;
  state: string;
  author: string;
  date: string;
  github_url: string;
}

export interface EvidenceItem {
  id: string;
  citation_label: string;
  source_type: string;
  title: string;
  snippet: string;
  author?: string;
  date?: string;
  github_url?: string;
  relevance_score: number;
  why_selected?: string;
}

export interface TimelineEvent {
  id: string;
  date: string | null;
  event_type: string;
  title: string;
  description?: string;
  author?: string;
  citation_id?: string;
  github_url?: string;
  merged?: boolean;
  state?: string;
  labels?: string[];
}

export interface AskResponse {
  question_id: string;
  answer: string;
  confidence: number;
  confidence_explanation: string;
  timeline: TimelineEvent[];
  evidence: EvidenceItem[];
  known_vs_inferred: {
    known: string[];
    inferred: string[];
    unknown: string[];
  };
  related_files: string[];
  follow_up_questions: string[];
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface GraphNode {
  id: string;
  type: string;
  label: string;
  data: Record<string, unknown>;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type: string;
  confidence: number;
}

export interface Hotspot {
  path: string;
  language: string;
  churn_score: number;
  author_count: number;
  risk_score: number;
  line_count: number;
}
