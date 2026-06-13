"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getFileTree, getFileContent, getFileHistory } from "@/lib/api";
import { FileTreeNode } from "@/lib/types";
import { FileTree } from "@/components/FileTree";
import { AskPanel } from "@/components/AskPanel";
import { Navbar } from "@/components/Navbar";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { formatDate, getLanguageColor, cn } from "@/lib/utils";
import { Loader2, GitCommit, Users, Clock, ArrowLeft, Pickaxe, History } from "lucide-react";
import Link from "next/link";
import dynamic from "next/dynamic";
import { use } from "react";

const MonacoEditor = dynamic(() => import("@monaco-editor/react").then(m => ({ default: m.Editor })), {
  ssr: false,
  loading: () => <div className="h-full flex items-center justify-center"><Loader2 className="animate-spin h-5 w-5 text-primary" /></div>,
});

export default function FilesPage({ params }: { params: Promise<{ repoId: string }> }) {
  const { repoId } = use(params);
  const [selectedFile, setSelectedFile] = useState<FileTreeNode | null>(null);
  const [showAsk, setShowAsk] = useState(false);
  const [showHistory, setShowHistory] = useState(false);

  const { data: tree, isLoading: treeLoading } = useQuery({
    queryKey: ["filetree", repoId],
    queryFn: () => getFileTree(repoId),
  });

  const { data: fileContent, isLoading: contentLoading } = useQuery({
    queryKey: ["filecontent", repoId, selectedFile?.path],
    queryFn: () => getFileContent(repoId, selectedFile!.path),
    enabled: !!selectedFile && selectedFile.type === "file",
  });

  const { data: fileHistory } = useQuery({
    queryKey: ["filehistory", repoId, selectedFile?.path],
    queryFn: () => getFileHistory(repoId, selectedFile!.path),
    enabled: !!selectedFile && showHistory,
  });

  const languageMap: Record<string, string> = {
    python: "python",
    javascript: "javascript",
    typescript: "typescript",
    go: "go",
    java: "java",
    rust: "rust",
    markdown: "markdown",
    yaml: "yaml",
    json: "json",
  };

  return (
    <>
      <Navbar />
      <div className="flex h-[calc(100vh-3.5rem)]">
        {/* Sidebar */}
        <div className="w-64 border-r border-border flex flex-col flex-shrink-0">
          <div className="p-3 border-b border-border/50">
            <Link href={`/repositories/${repoId}`}>
              <Button variant="ghost" size="sm" className="gap-1.5 text-xs">
                <ArrowLeft className="h-3.5 w-3.5" />
                Back to Dashboard
              </Button>
            </Link>
          </div>
          <div className="flex-1 overflow-y-auto p-2">
            {treeLoading ? (
              <div className="flex justify-center py-8">
                <Loader2 className="h-5 w-5 animate-spin text-primary" />
              </div>
            ) : tree ? (
              <FileTree
                nodes={tree}
                selectedPath={selectedFile?.path}
                onSelect={(node) => {
                  setSelectedFile(node);
                  setShowAsk(false);
                  setShowHistory(false);
                }}
              />
            ) : null}
          </div>
        </div>

        {/* Main content */}
        <div className="flex-1 flex overflow-hidden">
          {/* Code viewer */}
          <div className={cn("flex-1 flex flex-col overflow-hidden", (showAsk || showHistory) && "border-r border-border")}>
            {selectedFile ? (
              <>
                {/* File header */}
                <div className="flex items-center justify-between px-4 py-2 border-b border-border/50 bg-card/50">
                  <div className="flex items-center gap-2 min-w-0">
                    {selectedFile.language && (
                      <span className={cn("h-2 w-2 rounded-full flex-shrink-0", getLanguageColor(selectedFile.language))} />
                    )}
                    <span className="font-mono text-xs text-muted-foreground truncate">{selectedFile.path}</span>
                    {selectedFile.language && (
                      <Badge variant="ghost" className="text-xs">{selectedFile.language}</Badge>
                    )}
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <Button
                      size="sm"
                      variant="ghost"
                      className="gap-1.5 text-xs h-7"
                      onClick={() => { setShowHistory(!showHistory); setShowAsk(false); }}
                    >
                      <History className="h-3.5 w-3.5" />
                      History
                    </Button>
                    <Button
                      size="sm"
                      variant={showAsk ? "default" : "outline"}
                      className="gap-1.5 text-xs h-7"
                      onClick={() => { setShowAsk(!showAsk); setShowHistory(false); }}
                    >
                      <Pickaxe className="h-3.5 w-3.5" />
                      Ask why this exists
                    </Button>
                  </div>
                </div>

                {/* Code editor */}
                <div className="flex-1 overflow-hidden">
                  {contentLoading ? (
                    <div className="h-full flex items-center justify-center">
                      <Loader2 className="h-5 w-5 animate-spin text-primary" />
                    </div>
                  ) : fileContent ? (
                    <MonacoEditor
                      height="100%"
                      language={languageMap[fileContent.language || ""] || "plaintext"}
                      value={fileContent.content}
                      theme="vs-dark"
                      options={{
                        readOnly: true,
                        minimap: { enabled: true },
                        fontSize: 13,
                        lineNumbers: "on",
                        scrollBeyondLastLine: false,
                        wordWrap: "off",
                        automaticLayout: true,
                      }}
                    />
                  ) : null}
                </div>
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center text-muted-foreground">
                <div className="text-center">
                  <p className="text-sm">Select a file to view its contents</p>
                  <p className="text-xs mt-1 opacity-60">Click any file in the sidebar</p>
                </div>
              </div>
            )}
          </div>

          {/* Right panel: Ask or History */}
          {(showAsk || showHistory) && selectedFile && (
            <div className="w-96 flex-shrink-0 flex flex-col overflow-hidden">
              {showAsk && (
                <AskPanel
                  repoId={repoId}
                  contextFilePath={selectedFile.path}
                />
              )}
              {showHistory && fileHistory && (
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                  <h3 className="font-medium text-sm">File History</h3>
                  <div className="grid grid-cols-3 gap-2 text-center">
                    <Card className="p-2">
                      <GitCommit className="h-4 w-4 text-blue-400 mx-auto mb-1" />
                      <p className="text-sm font-bold">{fileHistory.commits.length}</p>
                      <p className="text-xs text-muted-foreground">Commits</p>
                    </Card>
                    <Card className="p-2">
                      <Users className="h-4 w-4 text-cyan-400 mx-auto mb-1" />
                      <p className="text-sm font-bold">{fileHistory.authors.length}</p>
                      <p className="text-xs text-muted-foreground">Authors</p>
                    </Card>
                    <Card className="p-2">
                      <Clock className="h-4 w-4 text-amber-400 mx-auto mb-1" />
                      <p className="text-sm font-bold">{Math.round(fileHistory.churn_score)}</p>
                      <p className="text-xs text-muted-foreground">Churn</p>
                    </Card>
                  </div>
                  <div className="space-y-2">
                    <p className="text-xs text-muted-foreground uppercase tracking-wide">Recent Commits</p>
                    {fileHistory.commits.slice(0, 10).map((c) => (
                      <div key={c.sha} className="rounded-md border border-border/50 p-2 text-xs">
                        <p className="font-medium line-clamp-1">{c.message}</p>
                        <div className="flex items-center gap-2 mt-0.5 text-muted-foreground">
                          <span>{c.author}</span>
                          <span>·</span>
                          <span>{formatDate(c.date)}</span>
                          <span className="text-green-400">+{c.additions}</span>
                          <span className="text-red-400">-{c.deletions}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
