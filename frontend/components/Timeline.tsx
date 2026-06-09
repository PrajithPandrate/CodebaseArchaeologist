"use client";

import { TimelineEvent } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { cn, formatDate } from "@/lib/utils";
import {
  GitCommit, GitPullRequest, GitMerge, CircleDot, CheckCircle2,
  MessageSquare, ExternalLink
} from "lucide-react";

interface Props {
  events: TimelineEvent[];
  onEventClick?: (event: TimelineEvent) => void;
}

const EVENT_CONFIG: Record<string, {
  icon: React.ReactNode;
  color: string;
  dotColor: string;
  label: string;
}> = {
  commit: {
    icon: <GitCommit className="h-3.5 w-3.5" />,
    color: "border-blue-500/30 bg-blue-500/10",
    dotColor: "bg-blue-400",
    label: "Commit",
  },
  pr_created: {
    icon: <GitPullRequest className="h-3.5 w-3.5" />,
    color: "border-purple-500/30 bg-purple-500/10",
    dotColor: "bg-purple-400",
    label: "PR Opened",
  },
  pr_merged: {
    icon: <GitMerge className="h-3.5 w-3.5" />,
    color: "border-purple-500/30 bg-purple-500/20",
    dotColor: "bg-purple-500",
    label: "PR Merged",
  },
  issue_opened: {
    icon: <CircleDot className="h-3.5 w-3.5" />,
    color: "border-amber-500/30 bg-amber-500/10",
    dotColor: "bg-amber-400",
    label: "Issue Opened",
  },
  issue_closed: {
    icon: <CheckCircle2 className="h-3.5 w-3.5" />,
    color: "border-emerald-500/30 bg-emerald-500/10",
    dotColor: "bg-emerald-400",
    label: "Issue Closed",
  },
  comment: {
    icon: <MessageSquare className="h-3.5 w-3.5" />,
    color: "border-cyan-500/30 bg-cyan-500/10",
    dotColor: "bg-cyan-400",
    label: "Comment",
  },
};

export function Timeline({ events, onEventClick }: Props) {
  if (!events.length) {
    return (
      <div className="flex items-center justify-center h-32 text-sm text-muted-foreground">
        No timeline events found.
      </div>
    );
  }

  return (
    <div className="relative space-y-0">
      {/* Vertical line */}
      <div className="absolute left-5 top-2 bottom-2 w-px bg-border/50" />

      {events.map((event, i) => {
        const config = EVENT_CONFIG[event.event_type] || {
          icon: <GitCommit className="h-3.5 w-3.5" />,
          color: "border-border bg-card",
          dotColor: "bg-muted-foreground",
          label: event.event_type,
        };

        return (
          <div key={event.id || i} className="flex gap-4 pb-4">
            {/* Dot */}
            <div className="flex-shrink-0 flex flex-col items-center pt-2.5">
              <div className={cn("h-2.5 w-2.5 rounded-full border-2 border-background z-10", config.dotColor)} />
            </div>

            {/* Content */}
            <div
              onClick={() => onEventClick?.(event)}
              className={cn(
                "flex-1 rounded-lg border p-3 text-sm transition-colors",
                config.color,
                onEventClick && "cursor-pointer hover:opacity-90"
              )}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className={cn("flex items-center gap-1 text-xs opacity-70", config.color.includes("blue") ? "text-blue-300" : config.color.includes("purple") ? "text-purple-300" : "text-amber-300")}>
                    {config.icon}
                    {config.label}
                  </span>
                  {event.labels?.map((l) => (
                    <Badge key={l} variant="outline" className="text-[10px] px-1 py-0">{l}</Badge>
                  ))}
                </div>
                <div className="flex items-center gap-1.5 flex-shrink-0">
                  <span className="text-xs text-muted-foreground">{event.date ? formatDate(event.date) : "?"}</span>
                  {event.github_url && (
                    <a
                      href={event.github_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <ExternalLink className="h-3 w-3 text-muted-foreground hover:text-foreground" />
                    </a>
                  )}
                </div>
              </div>
              <p className="font-medium mt-1">{event.title}</p>
              {event.description && (
                <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{event.description}</p>
              )}
              {event.author && (
                <p className="text-xs text-muted-foreground/60 mt-1">by {event.author}</p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
