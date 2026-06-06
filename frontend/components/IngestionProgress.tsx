"use client";

import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useEffect, useRef } from "react";
import { getIngestionStatus } from "@/lib/api";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { INGESTION_STAGES } from "@/lib/utils";
import { CheckCircle2, Circle, Loader2, XCircle, AlertCircle } from "lucide-react";

interface Props {
  repoId: string;
  jobId: string;
}

export function IngestionProgress({ repoId, jobId }: Props) {
  const router = useRouter();
  const logsEndRef = useRef<HTMLDivElement>(null);

  const { data: job } = useQuery({
    queryKey: ["ingestion", repoId, jobId],
    queryFn: () => getIngestionStatus(repoId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === "completed" || status === "failed") return false;
      return 2000;
    },
  });

  useEffect(() => {
    if (job?.status === "completed") {
      setTimeout(() => router.push(`/repositories/${repoId}`), 1500);
    }
  }, [job?.status, repoId, router]);

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [job?.logs?.length]);

  if (!job) {
    return (
      <div className="flex items-center justify-center h-48">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  const currentStageIdx = INGESTION_STAGES.findIndex((s) => s.key === job.current_stage);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">Ingestion Progress</CardTitle>
            <StatusBadge status={job.status} />
          </div>
          <Progress value={job.progress_percent} className="mt-3" />
          <p className="text-xs text-muted-foreground mt-1">{job.progress_percent}% complete</p>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {INGESTION_STAGES.map((stage, idx) => {
              const isDone = currentStageIdx > idx || job.status === "completed";
              const isActive = currentStageIdx === idx && job.status === "running";
              const isFailed = job.status === "failed" && isActive;

              return (
                <div key={stage.key} className="flex items-center gap-3">
                  <div className="flex-shrink-0">
                    {isFailed ? (
                      <XCircle className="h-4 w-4 text-destructive" />
                    ) : isDone ? (
                      <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                    ) : isActive ? (
                      <Loader2 className="h-4 w-4 animate-spin text-primary" />
                    ) : (
                      <Circle className="h-4 w-4 text-muted-foreground/30" />
                    )}
                  </div>
                  <span
                    className={`text-sm ${
                      isDone
                        ? "text-foreground"
                        : isActive
                        ? "text-primary font-medium"
                        : "text-muted-foreground/50"
                    }`}
                  >
                    {stage.label}
                  </span>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {job.error_message && (
        <Card className="border-destructive/40">
          <CardContent className="pt-4">
            <div className="flex items-start gap-2 text-destructive">
              <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
              <div>
                <p className="text-sm font-medium">Ingestion failed</p>
                <pre className="mt-1 text-xs whitespace-pre-wrap text-destructive/80">
                  {job.error_message}
                </pre>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm text-muted-foreground">Logs</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="bg-background rounded-md border border-border/50 p-3 font-mono text-xs space-y-0.5 max-h-72 overflow-y-auto">
            {(job.logs || []).map((log, i) => (
              <div key={i} className="flex gap-2 text-muted-foreground">
                <span className="text-muted-foreground/40 flex-shrink-0">
                  {new Date(log.ts).toLocaleTimeString()}
                </span>
                <span className="text-primary/70">[{log.stage}]</span>
                <span>{log.msg}</span>
              </div>
            ))}
            <div ref={logsEndRef} />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  if (status === "completed") return <Badge variant="success">Complete</Badge>;
  if (status === "failed") return <Badge variant="destructive">Failed</Badge>;
  if (status === "running") return <Badge variant="default">Running</Badge>;
  return <Badge variant="secondary">Queued</Badge>;
}
