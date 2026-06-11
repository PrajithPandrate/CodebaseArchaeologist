"use client";

import { Hotspot } from "@/lib/types";
import { cn, getLanguageColor } from "@/lib/utils";
import { Flame, Users, GitCommit, AlertTriangle } from "lucide-react";

interface Props {
  hotspots: Hotspot[];
  onSelect?: (path: string) => void;
}

export function HotspotCards({ hotspots, onSelect }: Props) {
  if (!hotspots.length) {
    return (
      <div className="flex items-center justify-center h-32 text-sm text-muted-foreground">
        No hotspots detected yet.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {hotspots.slice(0, 15).map((h) => (
        <HotspotRow key={h.path} hotspot={h} onSelect={onSelect} />
      ))}
    </div>
  );
}

function HotspotRow({ hotspot, onSelect }: { hotspot: Hotspot; onSelect?: (p: string) => void }) {
  const riskColor =
    hotspot.risk_score > 0.7
      ? "text-red-400 bg-red-500/10 border-red-500/20"
      : hotspot.risk_score > 0.4
      ? "text-amber-400 bg-amber-500/10 border-amber-500/20"
      : "text-emerald-400 bg-emerald-500/10 border-emerald-500/20";

  return (
    <button
      onClick={() => onSelect?.(hotspot.path)}
      className="w-full text-left rounded-lg border border-border bg-card/50 p-3 hover:border-primary/30 hover:bg-primary/5 transition-colors"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className={cn("h-2 w-2 rounded-full flex-shrink-0", getLanguageColor(hotspot.language))} />
            <span className="font-mono text-xs text-foreground truncate">{hotspot.path}</span>
          </div>
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            <span className="flex items-center gap-1">
              <Flame className="h-3 w-3 text-orange-400" />
              Churn: {Math.round(hotspot.churn_score).toLocaleString()}
            </span>
            <span className="flex items-center gap-1">
              <Users className="h-3 w-3" />
              {hotspot.author_count} authors
            </span>
            <span className="flex items-center gap-1">
              <GitCommit className="h-3 w-3" />
              {hotspot.line_count} lines
            </span>
          </div>
        </div>
        <div className={cn("flex items-center gap-1 rounded border px-2 py-0.5 text-xs font-medium flex-shrink-0", riskColor)}>
          <AlertTriangle className="h-3 w-3" />
          {Math.round(hotspot.risk_score * 100)}%
        </div>
      </div>
      {/* Risk bar */}
      <div className="mt-2 h-1 rounded-full bg-muted/30">
        <div
          className={cn("h-full rounded-full transition-all", hotspot.risk_score > 0.7 ? "bg-red-400" : hotspot.risk_score > 0.4 ? "bg-amber-400" : "bg-emerald-400")}
          style={{ width: `${Math.round(hotspot.risk_score * 100)}%` }}
        />
      </div>
    </button>
  );
}
