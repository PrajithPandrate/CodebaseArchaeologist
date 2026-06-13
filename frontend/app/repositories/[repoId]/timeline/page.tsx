"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getTimeline } from "@/lib/api";
import { Navbar } from "@/components/Navbar";
import { Timeline } from "@/components/Timeline";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Loader2, Search, ArrowLeft } from "lucide-react";
import Link from "next/link";
import { use } from "react";

export default function TimelinePage({ params }: { params: Promise<{ repoId: string }> }) {
  const { repoId } = use(params);
  const [keyword, setKeyword] = useState("");
  const [filePath, setFilePath] = useState("");
  const [filters, setFilters] = useState({ keyword: "", file_path: "" });

  const { data, isLoading } = useQuery({
    queryKey: ["timeline", repoId, filters],
    queryFn: () => getTimeline(repoId, filters),
  });

  const handleSearch = () => setFilters({ keyword, file_path: filePath });

  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-3xl px-4 py-6">
        <div className="flex items-center gap-3 mb-6">
          <Link href={`/repositories/${repoId}`}>
            <Button variant="ghost" size="icon" className="h-8 w-8">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <h1 className="text-xl font-bold">Timeline Investigation</h1>
            <p className="text-sm text-muted-foreground">Chronological history of commits, PRs, and issues</p>
          </div>
        </div>

        {/* Filters */}
        <div className="flex gap-2 mb-6 flex-wrap">
          <Input
            placeholder="Search keyword..."
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            className="flex-1 min-w-48"
          />
          <Input
            placeholder="Filter by file path..."
            value={filePath}
            onChange={(e) => setFilePath(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            className="flex-1 min-w-48"
          />
          <Button onClick={handleSearch} className="gap-2">
            <Search className="h-4 w-4" />
            Search
          </Button>
        </div>

        {isLoading ? (
          <div className="flex justify-center py-16">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        ) : (
          <>
            {data?.total !== undefined && (
              <p className="text-sm text-muted-foreground mb-4">{data.total} events found</p>
            )}
            <Timeline events={data?.events || []} />
          </>
        )}
      </main>
    </>
  );
}
