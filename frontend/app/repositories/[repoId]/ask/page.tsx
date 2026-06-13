"use client";

import { AskPanel } from "@/components/AskPanel";
import { Navbar } from "@/components/Navbar";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";
import { use } from "react";

export default function AskPage({ params }: { params: Promise<{ repoId: string }> }) {
  const { repoId } = use(params);

  return (
    <>
      <Navbar />
      <div className="flex flex-col h-[calc(100vh-3.5rem)]">
        <div className="border-b border-border/50 px-4 py-3 flex items-center gap-3">
          <Link href={`/repositories/${repoId}`}>
            <Button variant="ghost" size="icon" className="h-8 w-8">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <h1 className="font-semibold text-sm">Ask Archaeologist</h1>
        </div>
        <div className="flex-1 overflow-hidden">
          <AskPanel repoId={repoId} />
        </div>
      </div>
    </>
  );
}
