"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { createRepository, seedDemo } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Github, Lock, MessageSquare, GitCommit, FileText, Loader2, Pickaxe, Sparkles } from "lucide-react";

export function RepoImportForm() {
  const router = useRouter();
  const [url, setUrl] = useState("");
  const [token, setToken] = useState("");
  const [options, setOptions] = useState({
    include_issues: true,
    include_pr_comments: true,
    include_commit_diffs: true,
    include_docs: true,
  });

  const mutation = useMutation({
    mutationFn: createRepository,
    onSuccess: (data) => {
      toast.success("Repository queued for ingestion");
      router.push(`/repositories/${data.repository_id}/ingestion/${data.ingestion_job_id}`);
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "Failed to add repository";
      toast.error(msg);
    },
  });

  const demoMutation = useMutation({
    mutationFn: seedDemo,
    onSuccess: (data) => {
      toast.success("Demo repository loaded");
      router.push(`/repositories/${data.repository_id}`);
    },
    onError: () => toast.error("Failed to load demo"),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    mutation.mutate({
      github_url: url.trim(),
      github_token: token || undefined,
      ...options,
    });
  };

  const toggle = (key: keyof typeof options) =>
    setOptions((p) => ({ ...p, [key]: !p[key] }));

  return (
    <div className="space-y-6">
      <Card className="border-border/60">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Github className="h-5 w-5 text-primary" />
            Analyze a Repository
          </CardTitle>
          <CardDescription>
            Enter a public GitHub repository URL to begin archaeological excavation.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">GitHub Repository URL</label>
              <Input
                placeholder="https://github.com/owner/repo"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                disabled={mutation.isPending}
                className="font-mono text-sm"
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium flex items-center gap-1.5">
                <Lock className="h-3.5 w-3.5 text-muted-foreground" />
                GitHub Token
                <span className="text-muted-foreground font-normal">(optional — for private repos or higher rate limits)</span>
              </label>
              <Input
                type="password"
                placeholder="ghp_..."
                value={token}
                onChange={(e) => setToken(e.target.value)}
                disabled={mutation.isPending}
                className="font-mono text-sm"
              />
              <p className="text-xs text-muted-foreground">
                Token is used only during ingestion and never stored in full.
              </p>
            </div>

            <div className="space-y-3">
              <label className="text-sm font-medium">Include in analysis</label>
              <div className="grid grid-cols-2 gap-2">
                <CheckOption
                  icon={<MessageSquare className="h-3.5 w-3.5" />}
                  label="Issues"
                  checked={options.include_issues}
                  onChange={() => toggle("include_issues")}
                />
                <CheckOption
                  icon={<MessageSquare className="h-3.5 w-3.5" />}
                  label="PR Comments"
                  checked={options.include_pr_comments}
                  onChange={() => toggle("include_pr_comments")}
                />
                <CheckOption
                  icon={<GitCommit className="h-3.5 w-3.5" />}
                  label="Commit Diffs"
                  checked={options.include_commit_diffs}
                  onChange={() => toggle("include_commit_diffs")}
                />
                <CheckOption
                  icon={<FileText className="h-3.5 w-3.5" />}
                  label="README / Docs"
                  checked={options.include_docs}
                  onChange={() => toggle("include_docs")}
                />
              </div>
            </div>

            <Button
              type="submit"
              className="w-full"
              disabled={!url.trim() || mutation.isPending}
            >
              {mutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Starting ingestion...
                </>
              ) : (
                <>
                  <Pickaxe className="h-4 w-4" />
                  Start Ingestion
                </>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <span className="w-full border-t border-border/50" />
        </div>
        <div className="relative flex justify-center text-xs uppercase">
          <span className="bg-background px-2 text-muted-foreground">or</span>
        </div>
      </div>

      <Button
        variant="outline"
        className="w-full border-amber-500/30 text-amber-300 hover:bg-amber-500/10"
        onClick={() => demoMutation.mutate()}
        disabled={demoMutation.isPending}
      >
        {demoMutation.isPending ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Sparkles className="h-4 w-4" />
        )}
        Try the Demo (Payment Service with Retry History)
      </Button>
    </div>
  );
}

function CheckOption({
  icon,
  label,
  checked,
  onChange,
}: {
  icon: React.ReactNode;
  label: string;
  checked: boolean;
  onChange: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onChange}
      className={`flex items-center gap-2 rounded-md border px-3 py-2 text-sm transition-colors ${
        checked
          ? "border-primary/40 bg-primary/10 text-foreground"
          : "border-border bg-transparent text-muted-foreground hover:border-border/80"
      }`}
    >
      <div
        className={`h-3.5 w-3.5 rounded border flex items-center justify-center ${
          checked ? "border-primary bg-primary" : "border-muted-foreground"
        }`}
      >
        {checked && (
          <svg className="h-2.5 w-2.5 text-primary-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
          </svg>
        )}
      </div>
      {icon}
      {label}
    </button>
  );
}
