"use client";

import { EvidenceItem } from "@/lib/types";
import { getSourceBadgeColor, formatDate, confidenceLabel, cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ExternalLink, X, Info, GitCommit, GitPullRequest, CircleDot, MessageSquare, Code2, FileText } from "lucide-react";

interface Props {
  evidence: EvidenceItem | null;
  onClose: () => void;
}

const SOURCE_ICONS: Record<string, React.ReactNode> = {
  commit: <GitCommit className="h-4 w-4" />,
  pull_request: <GitPullRequest className="h-4 w-4" />,
  pr: <GitPullRequest className="h-4 w-4" />,
  issue: <CircleDot className="h-4 w-4" />,
  comment: <MessageSquare className="h-4 w-4" />,
  code: <Code2 className="h-4 w-4" />,
  doc: <FileText className="h-4 w-4" />,
};

export function EvidenceDrawer({ evidence, onClose }: Props) {
  if (!evidence) return null;

  const { label: confLabel, color: confColor } = confidenceLabel(evidence.relevance_score);

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full max-w-md animate-slide-in bg-card border-l border-border shadow-2xl overflow-y-auto">
        <div className="sticky top-0 z-10 flex items-center justify-between bg-card/95 backdrop-blur-sm border-b border-border px-4 py-3">
          <div className="flex items-center gap-2">
            {SOURCE_ICONS[evidence.source_type] || <Info className="h-4 w-4" />}
            <span className="font-medium text-sm">Evidence Detail</span>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        <div className="p-4 space-y-4">
          {/* Header */}
          <div className="space-y-2">
            <div className="flex items-center gap-2 flex-wrap">
              <span className={cn("inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs font-medium", getSourceBadgeColor(evidence.source_type))}>
                {SOURCE_ICONS[evidence.source_type]}
                {evidence.source_type.replace("_", " ")}
              </span>
              <Badge variant="ghost" className="text-xs font-mono">
                {evidence.citation_label}
              </Badge>
            </div>
            <h3 className="font-medium text-sm leading-snug">{evidence.title}</h3>
          </div>

          {/* Meta */}
          <div className="grid grid-cols-2 gap-3 rounded-md bg-muted/30 p-3 text-xs">
            {evidence.author && (
              <div>
                <p className="text-muted-foreground mb-0.5">Author</p>
                <p className="font-medium">{evidence.author}</p>
              </div>
            )}
            {evidence.date && (
              <div>
                <p className="text-muted-foreground mb-0.5">Date</p>
                <p className="font-medium">{formatDate(evidence.date)}</p>
              </div>
            )}
            <div>
              <p className="text-muted-foreground mb-0.5">Relevance</p>
              <p className={`font-medium ${confColor}`}>
                {confLabel} ({Math.round(evidence.relevance_score * 100)}%)
              </p>
            </div>
            <div>
              <p className="text-muted-foreground mb-0.5">Source</p>
              <p className="font-medium capitalize">{evidence.source_type.replace("_", " ")}</p>
            </div>
          </div>

          {/* Why selected */}
          {evidence.why_selected && (
            <div className="rounded-md border border-primary/20 bg-primary/5 px-3 py-2">
              <p className="text-xs text-muted-foreground mb-1">Why this was retrieved</p>
              <p className="text-xs text-primary/80">{evidence.why_selected}</p>
            </div>
          )}

          {/* Snippet */}
          <div>
            <p className="text-xs text-muted-foreground mb-2">Content</p>
            <pre className="bg-background border border-border rounded-md p-3 text-xs whitespace-pre-wrap font-mono leading-relaxed overflow-x-auto">
              {evidence.snippet}
            </pre>
          </div>

          {/* GitHub link */}
          {evidence.github_url && (
            <a
              href={evidence.github_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 rounded-md border border-border px-3 py-2 text-xs text-muted-foreground hover:text-foreground hover:border-primary/40 transition-colors"
            >
              <ExternalLink className="h-3.5 w-3.5" />
              View on GitHub
            </a>
          )}
        </div>
      </div>
    </div>
  );
}
