"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { askQuestion } from "@/lib/api";
import { AskResponse, EvidenceItem } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { EvidenceDrawer } from "./EvidenceDrawer";
import { getSourceBadgeColor, formatDate, confidenceLabel, cn } from "@/lib/utils";
import {
  Send, Loader2, ChevronRight, CheckCircle, HelpCircle,
  AlertCircle, GitCommit, GitPullRequest, CircleDot,
  MessageSquare, Code2, ExternalLink, Clock
} from "lucide-react";

interface Props {
  repoId: string;
  contextFilePath?: string;
  contextSymbol?: string;
  onFollowUp?: (q: string) => void;
}

const EXAMPLE_QUESTIONS = [
  "Why does this retry logic exist?",
  "What changed before the payment bug was fixed?",
  "Who understands the auth module best?",
  "Which PR introduced this behavior?",
  "Why was this caching layer added?",
];

export function AskPanel({ repoId, contextFilePath, contextSymbol, onFollowUp }: Props) {
  const [question, setQuestion] = useState("");
  const [response, setResponse] = useState<AskResponse | null>(null);
  const [selectedEvidence, setSelectedEvidence] = useState<EvidenceItem | null>(null);

  const mutation = useMutation({
    mutationFn: (q: string) =>
      askQuestion(repoId, q, contextFilePath ? { file_path: contextFilePath, symbol_name: contextSymbol } : undefined),
    onSuccess: (data) => setResponse(data),
    onError: () => toast.error("Failed to get answer. Make sure the repository is indexed."),
  });

  const handleAsk = (q: string) => {
    if (!q.trim()) return;
    setQuestion(q);
    mutation.mutate(q);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Context badge */}
      {contextFilePath && (
        <div className="px-4 py-2 border-b border-border/50 flex items-center gap-2 text-xs text-muted-foreground">
          <Code2 className="h-3 w-3" />
          <span className="font-mono">{contextFilePath}</span>
          {contextSymbol && (
            <>
              <ChevronRight className="h-3 w-3" />
              <span className="text-primary font-mono">{contextSymbol}</span>
            </>
          )}
        </div>
      )}

      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {/* Examples */}
        {!response && !mutation.isPending && (
          <div className="space-y-3">
            <p className="text-sm text-muted-foreground">Try asking:</p>
            <div className="space-y-2">
              {EXAMPLE_QUESTIONS.map((q) => (
                <button
                  key={q}
                  onClick={() => handleAsk(q)}
                  className="w-full text-left rounded-md border border-border/50 bg-card/50 px-3 py-2 text-sm text-muted-foreground hover:border-primary/40 hover:text-foreground transition-colors"
                >
                  <ChevronRight className="inline h-3 w-3 mr-1 text-primary" />
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Loading */}
        {mutation.isPending && (
          <div className="flex items-center gap-3 rounded-lg border border-primary/20 bg-primary/5 px-4 py-3">
            <Loader2 className="h-4 w-4 animate-spin text-primary" />
            <div>
              <p className="text-sm font-medium">Excavating history...</p>
              <p className="text-xs text-muted-foreground">Searching commits, PRs, issues, and code</p>
            </div>
          </div>
        )}

        {/* Response */}
        {response && !mutation.isPending && (
          <div className="space-y-5 animate-fade-in">
            {/* Question */}
            <div className="flex justify-end">
              <div className="max-w-[85%] rounded-lg bg-primary/10 border border-primary/20 px-4 py-2 text-sm">
                {question}
              </div>
            </div>

            {/* Answer */}
            <div className="space-y-4">
              <div className="rounded-lg border border-border bg-card p-4 space-y-3">
                <p className="text-sm leading-relaxed whitespace-pre-wrap">{response.answer}</p>

                {/* Confidence */}
                <div className="flex items-center gap-2 pt-1 border-t border-border/50">
                  <ConfidenceBar score={response.confidence} />
                  <span className="text-xs text-muted-foreground">{response.confidence_explanation}</span>
                </div>
              </div>

              {/* Timeline */}
              {response.timeline.length > 0 && (
                <TimelineSection events={response.timeline} />
              )}

              {/* Evidence */}
              {response.evidence.length > 0 && (
                <EvidenceSection
                  evidence={response.evidence}
                  onSelect={setSelectedEvidence}
                />
              )}

              {/* Known vs Inferred */}
              <KnownInferredSection data={response.known_vs_inferred} />

              {/* Related files */}
              {response.related_files.length > 0 && (
                <div className="rounded-md border border-border p-3 space-y-2">
                  <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Related Files</p>
                  <div className="flex flex-wrap gap-1.5">
                    {response.related_files.map((f) => (
                      <span key={f} className="font-mono text-xs bg-muted/50 rounded px-2 py-0.5">
                        {f}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Follow-up questions */}
              {response.follow_up_questions.length > 0 && (
                <div className="space-y-2">
                  <p className="text-xs text-muted-foreground">Follow-up questions:</p>
                  {response.follow_up_questions.map((q) => (
                    <button
                      key={q}
                      onClick={() => {
                        handleAsk(q);
                        onFollowUp?.(q);
                      }}
                      className="w-full text-left rounded-md border border-border/50 bg-card/30 px-3 py-2 text-xs text-muted-foreground hover:border-primary/40 hover:text-foreground transition-colors"
                    >
                      <ChevronRight className="inline h-3 w-3 mr-1 text-primary" />
                      {q}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="border-t border-border p-4">
        <div className="flex gap-2">
          <Textarea
            placeholder="Ask why this code exists, who added it, what changed..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleAsk(question);
              }
            }}
            disabled={mutation.isPending}
            rows={2}
            className="flex-1 resize-none text-sm"
          />
          <Button
            onClick={() => handleAsk(question)}
            disabled={!question.trim() || mutation.isPending}
            size="icon"
            className="self-end h-10 w-10 flex-shrink-0"
          >
            {mutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>
        <p className="text-xs text-muted-foreground mt-1.5">Enter to send, Shift+Enter for new line</p>
      </div>

      <EvidenceDrawer evidence={selectedEvidence} onClose={() => setSelectedEvidence(null)} />
    </div>
  );
}

function ConfidenceBar({ score }: { score: number }) {
  const { label, color } = confidenceLabel(score);
  return (
    <div className="flex items-center gap-1.5 flex-shrink-0">
      <div className="flex gap-0.5">
        {[1, 2, 3, 4, 5].map((i) => (
          <div
            key={i}
            className={cn(
              "h-1.5 w-3 rounded-sm",
              i <= Math.round(score * 5) ? color.replace("text-", "bg-") : "bg-muted/40"
            )}
          />
        ))}
      </div>
      <span className={cn("text-xs font-medium", color)}>{label} confidence</span>
    </div>
  );
}

function TimelineSection({ events }: { events: AskResponse["timeline"] }) {
  return (
    <div className="space-y-2">
      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide flex items-center gap-1.5">
        <Clock className="h-3 w-3" />
        Historical Timeline
      </p>
      <div className="space-y-2">
        {events.map((event, i) => (
          <div key={i} className="flex gap-3 text-sm">
            <div className="flex flex-col items-center">
              <div className={cn(
                "h-2 w-2 rounded-full mt-1.5 flex-shrink-0",
                event.event_type === "pr_merged" ? "bg-purple-400" :
                event.event_type === "issue_opened" ? "bg-amber-400" :
                event.event_type === "commit" ? "bg-blue-400" :
                "bg-muted-foreground/40"
              )} />
              {i < events.length - 1 && <div className="w-px flex-1 bg-border/50 mt-1" />}
            </div>
            <div className="pb-3">
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground">
                  {event.date ? formatDate(event.date) : "Unknown date"}
                </span>
                {event.citation_id && (
                  <span className="font-mono text-xs text-primary">{event.citation_id}</span>
                )}
              </div>
              <p className="text-xs font-medium mt-0.5">{event.title}</p>
              {event.description && (
                <p className="text-xs text-muted-foreground mt-0.5">{event.description}</p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function EvidenceSection({ evidence, onSelect }: { evidence: EvidenceItem[]; onSelect: (e: EvidenceItem) => void }) {
  return (
    <div className="space-y-2">
      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Evidence</p>
      <div className="space-y-1.5">
        {evidence.map((item) => (
          <button
            key={item.id}
            onClick={() => onSelect(item)}
            className="w-full text-left rounded-md border border-border/50 bg-card/50 p-2.5 hover:border-primary/30 hover:bg-primary/5 transition-colors"
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex items-center gap-2 min-w-0">
                <span className="font-mono text-xs text-primary flex-shrink-0">{item.citation_label}</span>
                <span className={cn("inline-flex items-center rounded border px-1.5 py-0.5 text-xs", getSourceBadgeColor(item.source_type))}>
                  {item.source_type.replace("_", " ")}
                </span>
              </div>
              <span className="text-xs text-muted-foreground flex-shrink-0">{Math.round(item.relevance_score * 100)}%</span>
            </div>
            <p className="text-xs font-medium mt-1 truncate">{item.title}</p>
            <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">{item.snippet}</p>
          </button>
        ))}
      </div>
    </div>
  );
}

function KnownInferredSection({ data }: { data: AskResponse["known_vs_inferred"] }) {
  if (!data.known.length && !data.inferred.length && !data.unknown.length) return null;

  return (
    <div className="rounded-md border border-border p-3 space-y-3 text-xs">
      <p className="font-medium text-muted-foreground uppercase tracking-wide">What Is Known vs Inferred</p>
      {data.known.length > 0 && (
        <div>
          <p className="text-emerald-400 font-medium mb-1 flex items-center gap-1">
            <CheckCircle className="h-3 w-3" /> Known
          </p>
          <ul className="space-y-0.5 text-muted-foreground">
            {data.known.map((f, i) => <li key={i} className="before:content-['•'] before:mr-1">{f}</li>)}
          </ul>
        </div>
      )}
      {data.inferred.length > 0 && (
        <div>
          <p className="text-amber-400 font-medium mb-1 flex items-center gap-1">
            <HelpCircle className="h-3 w-3" /> Inferred
          </p>
          <ul className="space-y-0.5 text-muted-foreground">
            {data.inferred.map((f, i) => <li key={i} className="before:content-['•'] before:mr-1">{f}</li>)}
          </ul>
        </div>
      )}
      {data.unknown.length > 0 && (
        <div>
          <p className="text-muted-foreground font-medium mb-1 flex items-center gap-1">
            <AlertCircle className="h-3 w-3" /> Unknown
          </p>
          <ul className="space-y-0.5 text-muted-foreground/60">
            {data.unknown.map((f, i) => <li key={i} className="before:content-['•'] before:mr-1">{f}</li>)}
          </ul>
        </div>
      )}
    </div>
  );
}
