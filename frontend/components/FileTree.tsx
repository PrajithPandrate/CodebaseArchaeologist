"use client";

import { useState } from "react";
import { FileTreeNode } from "@/lib/types";
import { cn, getLanguageColor } from "@/lib/utils";
import { ChevronRight, ChevronDown, Folder, FolderOpen, File } from "lucide-react";

interface Props {
  nodes: FileTreeNode[];
  selectedPath?: string;
  onSelect: (node: FileTreeNode) => void;
  depth?: number;
}

export function FileTree({ nodes, selectedPath, onSelect, depth = 0 }: Props) {
  return (
    <div className={cn("space-y-0.5", depth > 0 && "ml-3 border-l border-border/30 pl-2")}>
      {nodes.map((node) => (
        <FileTreeItem
          key={node.path}
          node={node}
          selectedPath={selectedPath}
          onSelect={onSelect}
          depth={depth}
        />
      ))}
    </div>
  );
}

function FileTreeItem({
  node,
  selectedPath,
  onSelect,
  depth,
}: {
  node: FileTreeNode;
  selectedPath?: string;
  onSelect: (node: FileTreeNode) => void;
  depth: number;
}) {
  const [expanded, setExpanded] = useState(depth < 2);

  const isSelected = selectedPath === node.path;
  const isDir = node.type === "directory";

  if (isDir) {
    return (
      <div>
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex w-full items-center gap-1.5 rounded px-2 py-1 text-xs text-muted-foreground hover:bg-secondary/50 hover:text-foreground transition-colors"
        >
          {expanded ? (
            <ChevronDown className="h-3 w-3 flex-shrink-0" />
          ) : (
            <ChevronRight className="h-3 w-3 flex-shrink-0" />
          )}
          {expanded ? (
            <FolderOpen className="h-3.5 w-3.5 flex-shrink-0 text-amber-400" />
          ) : (
            <Folder className="h-3.5 w-3.5 flex-shrink-0 text-amber-400" />
          )}
          <span className="truncate font-medium">{node.name}</span>
        </button>
        {expanded && node.children && (
          <FileTree
            nodes={node.children}
            selectedPath={selectedPath}
            onSelect={onSelect}
            depth={depth + 1}
          />
        )}
      </div>
    );
  }

  return (
    <button
      onClick={() => onSelect(node)}
      className={cn(
        "flex w-full items-center gap-1.5 rounded px-2 py-1 text-xs transition-colors",
        isSelected
          ? "bg-primary/15 text-foreground border border-primary/30"
          : "text-muted-foreground hover:bg-secondary/50 hover:text-foreground"
      )}
    >
      <span className="w-3 flex-shrink-0" />
      <File className="h-3.5 w-3.5 flex-shrink-0 text-muted-foreground/60" />
      <span className="truncate flex-1 text-left">{node.name}</span>
      {node.language && (
        <span
          className={cn("h-1.5 w-1.5 rounded-full flex-shrink-0", getLanguageColor(node.language))}
        />
      )}
      {node.churn_score && node.churn_score > 100 && (
        <span className="text-amber-400/70 flex-shrink-0 text-[10px]">⚡</span>
      )}
    </button>
  );
}
