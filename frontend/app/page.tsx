import Link from "next/link";
import { Pickaxe, GitBranch, Layers, MessageSquare, ArrowRight, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Nav */}
      <nav className="border-b border-border/50 bg-background/80 backdrop-blur-md">
        <div className="mx-auto flex h-14 max-w-screen-xl items-center justify-between px-6">
          <div className="flex items-center gap-2">
            <Pickaxe className="h-5 w-5 text-primary" />
            <span className="font-semibold text-gradient">Codebase Archaeologist</span>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/repositories">
              <Button variant="ghost" size="sm">Repositories</Button>
            </Link>
            <Link href="/repositories/new">
              <Button size="sm">Get Started</Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden px-6 py-24 sm:py-32">
        <div className="absolute inset-0 bg-gradient-to-b from-primary/5 via-transparent to-transparent" />
        <div className="relative mx-auto max-w-3xl text-center">
          <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-4 py-1.5 text-sm text-primary mb-8">
            <Sparkles className="h-3.5 w-3.5" />
            Evidence-based code history investigation
          </div>
          <h1 className="text-5xl sm:text-6xl font-bold tracking-tight mb-6">
            Understand the{" "}
            <span className="text-gradient">history</span>{" "}
            behind any codebase
          </h1>
          <p className="text-xl text-muted-foreground mb-10 leading-relaxed">
            Codebase Archaeologist connects code, commits, pull requests, issues,
            and comments to explain{" "}
            <em className="text-foreground not-italic font-medium">why code exists</em>.
          </p>
          <div className="flex items-center justify-center gap-4 flex-wrap">
            <Link href="/repositories/new">
              <Button size="lg" className="gap-2">
                <Pickaxe className="h-4 w-4" />
                Analyze a Repository
              </Button>
            </Link>
            <Link href="/repositories/new?demo=1">
              <Button variant="outline" size="lg" className="gap-2">
                <Sparkles className="h-4 w-4" />
                View Demo
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Feature cards */}
      <section className="mx-auto max-w-5xl px-6 pb-24">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          <FeatureCard
            icon={<GitBranch className="h-6 w-6 text-blue-400" />}
            title="Trace Code to Commits"
            description="Select any function or file and see every commit that introduced, modified, or deleted it — with full diffs and author attribution."
            color="border-blue-500/20 bg-blue-500/5"
          />
          <FeatureCard
            icon={<Layers className="h-6 w-6 text-purple-400" />}
            title="Find PRs and Issues Behind Decisions"
            description="Every piece of code can be traced back to the pull request, issue, and review discussion that motivated it."
            color="border-purple-500/20 bg-purple-500/5"
          />
          <FeatureCard
            icon={<MessageSquare className="h-6 w-6 text-emerald-400" />}
            title="Ask Questions with Cited Answers"
            description="Ask natural language questions and get answers backed by real evidence — commits, PRs, issues, and review comments."
            color="border-emerald-500/20 bg-emerald-500/5"
          />
        </div>

        {/* Demo scenario */}
        <div className="mt-16 rounded-xl border border-border bg-card/50 p-8">
          <h2 className="text-xl font-semibold mb-2">Primary Demo Scenario</h2>
          <p className="text-muted-foreground text-sm mb-6">
            A user clicks the retry function in a payment service and asks <em>&quot;Why was this retry logic added?&quot;</em>
          </p>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {[
              { num: "1", label: "Short explanation", desc: "3-6 sentence answer with inline citations" },
              { num: "2", label: "Historical timeline", desc: "Issue → PR → commits → merge → later refactor" },
              { num: "3", label: "Source citations", desc: "Commit messages, PR comments, issue discussions" },
              { num: "4", label: "Confidence score", desc: "0–1 score with explanation of uncertainty" },
            ].map((item) => (
              <div key={item.num} className="rounded-lg border border-border/50 p-4">
                <div className="h-7 w-7 rounded-full bg-primary/20 text-primary text-sm font-bold flex items-center justify-center mb-2">
                  {item.num}
                </div>
                <p className="text-sm font-medium mb-1">{item.label}</p>
                <p className="text-xs text-muted-foreground">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-border/50 py-16 px-6 text-center">
        <h2 className="text-2xl font-semibold mb-3">Ready to excavate your codebase?</h2>
        <p className="text-muted-foreground mb-6 text-sm">
          Supports repositories up to 10,000 files. GitHub token optional for private repos.
        </p>
        <Link href="/repositories/new">
          <Button size="lg" className="gap-2">
            Start Analyzing
            <ArrowRight className="h-4 w-4" />
          </Button>
        </Link>
      </section>
    </div>
  );
}

function FeatureCard({
  icon,
  title,
  description,
  color,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
  color: string;
}) {
  return (
    <div className={`rounded-xl border p-6 ${color}`}>
      <div className="mb-4">{icon}</div>
      <h3 className="font-semibold mb-2">{title}</h3>
      <p className="text-sm text-muted-foreground leading-relaxed">{description}</p>
    </div>
  );
}
