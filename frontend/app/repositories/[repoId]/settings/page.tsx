"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getRepository, deleteRepository, reindexRepository } from "@/lib/api";
import { Navbar } from "@/components/Navbar";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { formatDate } from "@/lib/utils";
import { useRouter } from "next/navigation";
import { Loader2, RefreshCw, Trash2, ArrowLeft, AlertTriangle } from "lucide-react";
import Link from "next/link";
import { use } from "react";

export default function SettingsPage({ params }: { params: Promise<{ repoId: string }> }) {
  const { repoId } = use(params);
  const router = useRouter();
  const queryClient = useQueryClient();
  const [confirmDelete, setConfirmDelete] = useState(false);

  const { data: repo, isLoading } = useQuery({
    queryKey: ["repository", repoId],
    queryFn: () => getRepository(repoId),
  });

  const reindexMutation = useMutation({
    mutationFn: () => reindexRepository(repoId),
    onSuccess: () => {
      toast.success("Re-indexing started");
      queryClient.invalidateQueries({ queryKey: ["repository", repoId] });
      router.push(`/repositories/${repoId}/ingestion/latest`);
    },
    onError: () => toast.error("Failed to start re-indexing"),
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteRepository(repoId),
    onSuccess: () => {
      toast.success("Repository deleted");
      router.push("/repositories");
    },
    onError: () => toast.error("Failed to delete repository"),
  });

  if (isLoading || !repo) {
    return (
      <>
        <Navbar />
        <div className="flex justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </>
    );
  }

  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-2xl px-4 py-6">
        <div className="flex items-center gap-3 mb-6">
          <Link href={`/repositories/${repoId}`}>
            <Button variant="ghost" size="icon" className="h-8 w-8">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <h1 className="text-xl font-bold">Settings</h1>
        </div>

        <div className="space-y-4">
          {/* Repository Info */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">{repo.owner}/{repo.name}</CardTitle>
              <CardDescription>{repo.github_url}</CardDescription>
            </CardHeader>
            <CardContent className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <p className="text-muted-foreground text-xs mb-0.5">Status</p>
                <Badge variant={repo.status === "ready" ? "success" : "default"}>{repo.status}</Badge>
              </div>
              <div>
                <p className="text-muted-foreground text-xs mb-0.5">Default Branch</p>
                <p className="font-mono">{repo.default_branch}</p>
              </div>
              <div>
                <p className="text-muted-foreground text-xs mb-0.5">Created</p>
                <p>{formatDate(repo.created_at)}</p>
              </div>
              <div>
                <p className="text-muted-foreground text-xs mb-0.5">Last Updated</p>
                <p>{formatDate(repo.updated_at)}</p>
              </div>
            </CardContent>
          </Card>

          {/* Re-index */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Re-run Ingestion</CardTitle>
              <CardDescription>
                Pull latest commits and re-index the repository. Existing data will be replaced.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button
                variant="outline"
                className="gap-2"
                onClick={() => reindexMutation.mutate()}
                disabled={reindexMutation.isPending}
              >
                {reindexMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="h-4 w-4" />
                )}
                Re-index Repository
              </Button>
            </CardContent>
          </Card>

          {/* Delete */}
          <Card className="border-destructive/30">
            <CardHeader>
              <CardTitle className="text-base text-destructive flex items-center gap-2">
                <AlertTriangle className="h-4 w-4" />
                Danger Zone
              </CardTitle>
              <CardDescription>
                Permanently delete this repository and all its indexed data. This cannot be undone.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {!confirmDelete ? (
                <Button
                  variant="outline"
                  className="gap-2 border-destructive/40 text-destructive hover:bg-destructive/10"
                  onClick={() => setConfirmDelete(true)}
                >
                  <Trash2 className="h-4 w-4" />
                  Delete Repository
                </Button>
              ) : (
                <div className="space-y-3">
                  <p className="text-sm text-destructive">
                    Are you sure? This will delete all commits, PRs, issues, code chunks, and embeddings for{" "}
                    <strong>{repo.owner}/{repo.name}</strong>.
                  </p>
                  <div className="flex gap-2">
                    <Button
                      variant="destructive"
                      className="gap-2"
                      onClick={() => deleteMutation.mutate()}
                      disabled={deleteMutation.isPending}
                    >
                      {deleteMutation.isPending ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Trash2 className="h-4 w-4" />
                      )}
                      Yes, Delete Everything
                    </Button>
                    <Button variant="ghost" onClick={() => setConfirmDelete(false)}>
                      Cancel
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </main>
    </>
  );
}
