"use client";

import { useQuery } from "@tanstack/react-query";
import { getRepository, getStats } from "@/lib/api";
import { Navbar } from "@/components/Navbar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { HotspotCards } from "@/components/HotspotCards";
import { formatDate, formatRelativeDate } from "@/lib/utils";
import Link from "next/link";
import {
  GitFork, GitCommit, GitPullRequest, CircleDot, Users,
  Files, Calendar, Loader2, MessageSquare, Pickaxe,
  TrendingUp, Clock, BarChart3, Code2
} from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid
} from "recharts";
import { use } from "react";

export default function RepositoryDashboard({ params }: { params: Promise<{ repoId: string }> }) {
  const { repoId } = use(params);

  const { data: repo, isLoading } = useQuery({
    queryKey: ["repository", repoId],
    queryFn: () => getRepository(repoId),
  });

  const { data: stats } = useQuery({
    queryKey: ["stats", repoId],
    queryFn: () => getStats(repoId),
    enabled: repo?.status === "ready",
  });

  if (isLoading) {
    return (
      <>
        <Navbar />
        <div className="flex justify-center items-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </>
    );
  }

  if (!repo) return null;

  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-screen-xl px-4 py-6">
        {/* Header */}
        <div className="flex items-start justify-between mb-6 flex-wrap gap-4">
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-2xl font-bold">{repo.owner}/{repo.name}</h1>
              <Badge variant={repo.status === "ready" ? "success" : "default"}>
                {repo.status}
              </Badge>
            </div>
            <a href={repo.github_url} target="_blank" rel="noopener noreferrer" className="text-sm text-muted-foreground hover:text-foreground flex items-center gap-1 mt-1">
              <GitFork className="h-3.5 w-3.5" />
              {repo.github_url}
            </a>
          </div>
          <div className="flex items-center gap-2">
            <Link href={`/repositories/${repoId}/ask`}>
              <Button className="gap-2">
                <Pickaxe className="h-4 w-4" />
                Ask Archaeologist
              </Button>
            </Link>
            <Link href={`/repositories/${repoId}/files`}>
              <Button variant="outline" className="gap-2">
                <Files className="h-4 w-4" />
                Explore Code
              </Button>
            </Link>
          </div>
        </div>

        {/* Nav tabs */}
        <div className="flex gap-1 mb-6 border-b border-border/50 pb-1 overflow-x-auto">
          {[
            { label: "Dashboard", href: `/repositories/${repoId}`, icon: <BarChart3 className="h-3.5 w-3.5" /> },
            { label: "Files", href: `/repositories/${repoId}/files`, icon: <Files className="h-3.5 w-3.5" /> },
            { label: "Ask", href: `/repositories/${repoId}/ask`, icon: <Pickaxe className="h-3.5 w-3.5" /> },
            { label: "Timeline", href: `/repositories/${repoId}/timeline`, icon: <Clock className="h-3.5 w-3.5" /> },
            { label: "Graph", href: `/repositories/${repoId}/graph`, icon: <TrendingUp className="h-3.5 w-3.5" /> },
            { label: "Settings", href: `/repositories/${repoId}/settings`, icon: <Code2 className="h-3.5 w-3.5" /> },
          ].map((tab) => (
            <Link
              key={tab.href}
              href={tab.href}
              className="flex items-center gap-1.5 rounded px-3 py-1.5 text-sm text-muted-foreground hover:bg-secondary/50 hover:text-foreground transition-colors whitespace-nowrap"
            >
              {tab.icon}
              {tab.label}
            </Link>
          ))}
        </div>

        {/* Stats grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
          <StatCard icon={<Files className="h-4 w-4 text-blue-400" />} label="Files" value={stats?.total_files} />
          <StatCard icon={<GitCommit className="h-4 w-4 text-green-400" />} label="Commits" value={stats?.total_commits} />
          <StatCard icon={<GitPullRequest className="h-4 w-4 text-purple-400" />} label="Pull Requests" value={stats?.total_prs} />
          <StatCard icon={<CircleDot className="h-4 w-4 text-amber-400" />} label="Issues" value={stats?.total_issues} />
          <StatCard icon={<Users className="h-4 w-4 text-cyan-400" />} label="Authors" value={stats?.total_authors} />
          <StatCard
            icon={<Calendar className="h-4 w-4 text-slate-400" />}
            label="First Commit"
            value={stats?.oldest_commit ? formatDate(stats.oldest_commit) : "—"}
            small
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Commits over time */}
          <Card className="lg:col-span-2">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <BarChart3 className="h-4 w-4 text-primary" />
                Commits Over Time
              </CardTitle>
            </CardHeader>
            <CardContent>
              {stats?.commits_over_time?.length ? (
                <ResponsiveContainer width="100%" height={180}>
                  <BarChart data={stats.commits_over_time.map((d) => ({
                    month: d.month ? new Date(d.month).toLocaleDateString("en", { month: "short", year: "2-digit" }) : "",
                    count: d.count,
                  }))}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(222 47% 15%)" />
                    <XAxis dataKey="month" tick={{ fill: "hsl(215 20% 55%)", fontSize: 11 }} />
                    <YAxis tick={{ fill: "hsl(215 20% 55%)", fontSize: 11 }} />
                    <Tooltip
                      contentStyle={{
                        background: "hsl(222 47% 9%)",
                        border: "1px solid hsl(222 47% 15%)",
                        borderRadius: "6px",
                        fontSize: "12px",
                      }}
                    />
                    <Bar dataKey="count" fill="hsl(210 100% 56%)" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-44 flex items-center justify-center text-sm text-muted-foreground">No commit data</div>
              )}
            </CardContent>
          </Card>

          {/* Top authors */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <Users className="h-4 w-4 text-primary" />
                Top Authors
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {stats?.top_authors?.slice(0, 8).map((a) => (
                  <div key={a.name} className="flex items-center gap-2 text-sm">
                    <div className="h-6 w-6 rounded-full bg-secondary flex items-center justify-center text-xs text-muted-foreground flex-shrink-0">
                      {a.name.charAt(0).toUpperCase()}
                    </div>
                    <span className="flex-1 truncate text-xs">{a.name}</span>
                    <span className="text-xs text-muted-foreground">{a.commit_count}</span>
                  </div>
                )) || <p className="text-sm text-muted-foreground">No data</p>}
              </div>
            </CardContent>
          </Card>

          {/* Hotspots */}
          <Card className="lg:col-span-2">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-primary" />
                  Code Hotspots
                  <span className="text-xs text-muted-foreground font-normal">(high churn + multiple authors)</span>
                </CardTitle>
                <Link href={`/repositories/${repoId}/files`}>
                  <Button variant="ghost" size="sm" className="text-xs h-7">View all</Button>
                </Link>
              </div>
            </CardHeader>
            <CardContent>
              {stats?.top_churn_files?.length ? (
                <div className="space-y-2">
                  {stats.top_churn_files.slice(0, 6).map((f) => (
                    <div key={f.path} className="flex items-center gap-3 text-xs">
                      <Link href={`/repositories/${repoId}/files?path=${encodeURIComponent(f.path)}`} className="font-mono text-muted-foreground hover:text-foreground truncate flex-1">
                        {f.path}
                      </Link>
                      <span className="text-muted-foreground/60 flex-shrink-0">churn: {Math.round(f.churn_score).toLocaleString()}</span>
                      <span className="text-muted-foreground/60 flex-shrink-0">{f.author_count} authors</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">No hotspot data</p>
              )}
            </CardContent>
          </Card>

          {/* Quick actions */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {[
                { label: "Ask a question", href: `/repositories/${repoId}/ask`, icon: <Pickaxe className="h-3.5 w-3.5" /> },
                { label: "Browse files", href: `/repositories/${repoId}/files`, icon: <Files className="h-3.5 w-3.5" /> },
                { label: "View timeline", href: `/repositories/${repoId}/timeline`, icon: <Clock className="h-3.5 w-3.5" /> },
                { label: "Knowledge graph", href: `/repositories/${repoId}/graph`, icon: <TrendingUp className="h-3.5 w-3.5" /> },
              ].map((action) => (
                <Link key={action.href} href={action.href}>
                  <Button variant="outline" size="sm" className="w-full justify-start gap-2 text-xs">
                    {action.icon}
                    {action.label}
                  </Button>
                </Link>
              ))}
            </CardContent>
          </Card>
        </div>
      </main>
    </>
  );
}

function StatCard({
  icon,
  label,
  value,
  small = false,
}: {
  icon: React.ReactNode;
  label: string;
  value?: number | string | null;
  small?: boolean;
}) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center gap-2 mb-1">
          {icon}
          <span className="text-xs text-muted-foreground">{label}</span>
        </div>
        <p className={`font-bold ${small ? "text-base" : "text-2xl"}`}>
          {value !== undefined && value !== null
            ? typeof value === "number"
              ? value.toLocaleString()
              : value
            : "—"}
        </p>
      </CardContent>
    </Card>
  );
}
