import { RepoImportForm } from "@/components/RepoImportForm";
import { Navbar } from "@/components/Navbar";
import { Pickaxe } from "lucide-react";

export default function NewRepositoryPage() {
  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-lg px-4 py-12">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center h-12 w-12 rounded-full bg-primary/10 mb-4">
            <Pickaxe className="h-6 w-6 text-primary" />
          </div>
          <h1 className="text-2xl font-bold">Analyze a Repository</h1>
          <p className="text-muted-foreground text-sm mt-2">
            Enter a GitHub URL to begin indexing commits, PRs, issues, and code.
          </p>
        </div>
        <RepoImportForm />
      </main>
    </>
  );
}
