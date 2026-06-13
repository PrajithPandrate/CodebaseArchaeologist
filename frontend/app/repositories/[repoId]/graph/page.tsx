"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getKnowledgeGraph } from "@/lib/api";
import { Navbar } from "@/components/Navbar";
import { KnowledgeGraph } from "@/components/KnowledgeGraph";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Loader2, Search, ArrowLeft } from "lucide-react";
import Link from "next/link";
import { use } from "react";

export default function GraphPage({ params }: { params: Promise<{ repoId: string }> }) {
  const { repoId } = use(params);
  const [filePath, setFilePath] = useState("");
  const [queryFilePath, setQueryFilePath] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["graph", repoId, queryFilePath],
    queryFn: () => getKnowledgeGraph(repoId, queryFilePath ? { file_path: queryFilePath } : {}),
  });

  return (
    <>
      <Navbar />
      <div className="flex flex-col h-[calc(100vh-3.5rem)]">
        <div className="flex items-center gap-3 px-4 py-3 border-b border-border/50">
          <Link href={`/repositories/${repoId}`}>
            <Button variant="ghost" size="icon" className="h-8 w-8">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <h1 className="font-semibold text-sm">Knowledge Graph</h1>
            <p className="text-xs text-muted-foreground">Relationships between files, commits, PRs, and issues</p>
          </div>
          <div className="ml-auto flex gap-2">
            <Input
              placeholder="Filter by file path..."
              value={filePath}
              onChange={(e) => setFilePath(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && setQueryFilePath(filePath)}
              className="w-64 h-8 text-xs"
            />
            <Button size="sm" onClick={() => setQueryFilePath(filePath)} className="gap-1.5 h-8 text-xs">
              <Search className="h-3.5 w-3.5" />
              Filter
            </Button>
          </div>
        </div>
        <div className="flex-1 relative">
          {isLoading ? (
            <div className="absolute inset-0 flex items-center justify-center">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          ) : data ? (
            <KnowledgeGraph data={data} />
          ) : null}
        </div>

        {/* Legend */}
        <div className="border-t border-border/50 px-4 py-2 flex items-center gap-4 text-xs text-muted-foreground flex-wrap">
          <span>Legend:</span>
          {[
            { color: "bg-blue-500", label: "File" },
            { color: "bg-green-500", label: "Commit" },
            { color: "bg-purple-500", label: "Pull Request" },
            { color: "bg-amber-500", label: "Issue" },
            { color: "bg-cyan-500", label: "Comment" },
          ].map(({ color, label }) => (
            <span key={label} className="flex items-center gap-1">
              <span className={`h-2 w-2 rounded-full ${color}`} />
              {label}
            </span>
          ))}
        </div>
      </div>
    </>
  );
}
