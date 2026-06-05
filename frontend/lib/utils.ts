import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { formatDistanceToNow, format } from "date-fns";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: string | null | undefined): string {
  if (!date) return "Unknown";
  try {
    return format(new Date(date), "MMM d, yyyy");
  } catch {
    return "Invalid date";
  }
}

export function formatRelativeDate(date: string | null | undefined): string {
  if (!date) return "Unknown";
  try {
    return formatDistanceToNow(new Date(date), { addSuffix: true });
  } catch {
    return "Unknown";
  }
}

export function getSourceIcon(sourceType: string): string {
  const icons: Record<string, string> = {
    commit: "git-commit",
    pull_request: "git-pull-request",
    pr: "git-pull-request",
    issue: "circle-dot",
    comment: "message-square",
    code: "code-2",
    doc: "file-text",
  };
  return icons[sourceType] || "file";
}

export function getSourceColor(sourceType: string): string {
  const colors: Record<string, string> = {
    commit: "text-blue-400",
    pull_request: "text-purple-400",
    pr: "text-purple-400",
    issue: "text-amber-400",
    comment: "text-cyan-400",
    code: "text-emerald-400",
    doc: "text-slate-400",
  };
  return colors[sourceType] || "text-slate-400";
}

export function getSourceBadgeColor(sourceType: string): string {
  const colors: Record<string, string> = {
    commit: "bg-blue-500/20 text-blue-300 border-blue-500/30",
    pull_request: "bg-purple-500/20 text-purple-300 border-purple-500/30",
    pr: "bg-purple-500/20 text-purple-300 border-purple-500/30",
    issue: "bg-amber-500/20 text-amber-300 border-amber-500/30",
    comment: "bg-cyan-500/20 text-cyan-300 border-cyan-500/30",
    code: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
    doc: "bg-slate-500/20 text-slate-300 border-slate-500/30",
  };
  return colors[sourceType] || "bg-slate-500/20 text-slate-300 border-slate-500/30";
}

export function confidenceLabel(score: number): { label: string; color: string } {
  if (score >= 0.8) return { label: "High", color: "text-emerald-400" };
  if (score >= 0.5) return { label: "Medium", color: "text-amber-400" };
  return { label: "Low", color: "text-red-400" };
}

export function getLanguageColor(language: string | null | undefined): string {
  const colors: Record<string, string> = {
    python: "bg-blue-500",
    javascript: "bg-yellow-500",
    typescript: "bg-blue-400",
    go: "bg-cyan-500",
    rust: "bg-orange-500",
    java: "bg-red-500",
    kotlin: "bg-purple-500",
    ruby: "bg-red-400",
    cpp: "bg-blue-600",
    c: "bg-gray-500",
    markdown: "bg-slate-400",
    yaml: "bg-green-400",
    json: "bg-amber-400",
  };
  return colors[language?.toLowerCase() || ""] || "bg-slate-600";
}

export function truncate(text: string, length: number): string {
  if (text.length <= length) return text;
  return text.slice(0, length) + "...";
}

export const INGESTION_STAGES = [
  { key: "queued", label: "Job queued" },
  { key: "cloning", label: "Cloning repository" },
  { key: "parsing_files", label: "Parsing file tree" },
  { key: "chunking", label: "Chunking source code" },
  { key: "git_history", label: "Reading git history" },
  { key: "commit_changes", label: "Indexing commit changes" },
  { key: "churn", label: "Computing churn scores" },
  { key: "github_prs", label: "Fetching GitHub PRs & issues" },
  { key: "relationships", label: "Building relationship graph" },
  { key: "embeddings", label: "Generating embeddings" },
  { key: "ready", label: "Ready" },
];
