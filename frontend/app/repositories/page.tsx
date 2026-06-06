"use client";

import { useQuery } from "@tanstack/react-query";
import { listRepositories } from "@/lib/api";
import { Navbar } from "@/components/Navbar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { formatRelativeDate } from "@/lib/utils";
import Link from "next/link";
import {
  Plus, Loader2, GitFork, Clock, CheckCircle2,
  Loader, AlertCircle, Circle, Pickaxe
} from "lucide-react";

export default function RepositoriesPage() {
  const { data: repos, isLoading } = useQuery({
    queryKey: ["repositories"],
    queryFn: listRepositories,
    refetchInterval: 5000,
  });

  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-4xl px-4 py-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold">Repositories</h1>
            <p className="text-sm text-muted-foreground mt-1">Your indexed codebases</p>
          </div>
          <Link href="/repositories/new">
            <Button className="gap-2">
              <Plus className="h-4 w-4" />
              Add Repository
            </Button>
          </Link>
        </div>

        {isLoading ? (
          <div className="flex justify-center py-16">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        ) : !repos?.length ? (
          <div className="text-center py-20 space-y-4">
            <Pickaxe className="h-12 w-12 text-muted-foreground/30 mx-auto" />
            <div>
              <p className="text-lg font-medium">No repositories yet</p>
              <p className="text-sm text-muted-foreground mt-1">
                Add a GitHub repository to start investigating its history
              </p>
            </div>
            <Link href="/repositories/new">
              <Button className="mt-2">
                <Plus className="h-4 w-4 mr-2" />
                Add Repository
              </Button>
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {repos.map((repo) => (
              <RepoCard key={repo.id} repo={repo} />
            ))}
          </div>
        )}
      </main>
    </>
  );
}

function RepoCard({ repo }: { repo: ReturnType<typeof listRepositories> extends Promise<infer T> ? T[0] : never }) {
  const statusConfig = {
    ready: { icon: <CheckCircle2 className="h-4 w-4 text-emerald-400" />, badge: <Badge variant="success">Ready</Badge> },
    ingesting: { icon: <Loader className="h-4 w-4 animate-spin text-primary" />, badge: <Badge variant="default">Ingesting</Badge> },
    pending: { icon: <Circle className="h-4 w-4 text-muted-foreground" />, badge: <Badge variant="secondary">Pending</Badge> },
    failed: { icon: <AlertCircle className="h-4 w-4 text-destructive" />, badge: <Badge variant="destructive">Failed</Badge> },
  }[repo.status] || { icon: null, badge: null };

  return (
    <Card className="card-hover">
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-3 min-w-0">
            {statusConfig.icon}
            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-semibold text-sm">
                  {repo.owner}/{repo.name}
                </span>
                {statusConfig.badge}
              </div>
              <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                <span className="flex items-center gap-1">
                  <GitFork className="h-3 w-3" />
                  <a href={repo.github_url} target="_blank" rel="noopener noreferrer" className="hover:text-foreground truncate max-w-[300px]">
                    {repo.github_url}
                  </a>
                </span>
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {formatRelativeDate(repo.created_at)}
                </span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            {repo.status === "ready" && (
              <Link href={`/repositories/${repo.id}`}>
                <Button size="sm" variant="outline">Explore</Button>
              </Link>
            )}
            {repo.status === "ingesting" && (
              <Link href={`/repositories/${repo.id}/ingestion/latest`}>
                <Button size="sm" variant="ghost">View Progress</Button>
              </Link>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
