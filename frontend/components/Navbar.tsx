"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { GitBranch, Pickaxe } from "lucide-react";

export function Navbar() {
  const pathname = usePathname();

  return (
    <nav className="sticky top-0 z-50 border-b border-border/50 bg-background/80 backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-screen-2xl items-center gap-6 px-4">
        <Link href="/" className="flex items-center gap-2">
          <Pickaxe className="h-5 w-5 text-primary" />
          <span className="font-semibold text-gradient">Codebase Archaeologist</span>
        </Link>
        <div className="flex items-center gap-1 text-sm">
          <NavLink href="/repositories" active={pathname.startsWith("/repositories")}>
            Repositories
          </NavLink>
        </div>
        <div className="ml-auto flex items-center gap-3 text-xs text-muted-foreground">
          <GitBranch className="h-4 w-4" />
          <span>Ask why code exists, not just what it does.</span>
        </div>
      </div>
    </nav>
  );
}

function NavLink({
  href,
  active,
  children,
}: {
  href: string;
  active: boolean;
  children: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      className={cn(
        "rounded-md px-3 py-1.5 text-sm transition-colors",
        active
          ? "bg-secondary text-foreground"
          : "text-muted-foreground hover:bg-secondary/50 hover:text-foreground"
      )}
    >
      {children}
    </Link>
  );
}
