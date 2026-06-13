import { IngestionProgress } from "@/components/IngestionProgress";
import { Navbar } from "@/components/Navbar";

interface Props {
  params: Promise<{ repoId: string; jobId: string }>;
}

export default async function IngestionPage({ params }: Props) {
  const { repoId, jobId } = await params;
  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-2xl px-4 py-8">
        <h1 className="text-xl font-bold mb-6">Repository Ingestion</h1>
        <IngestionProgress repoId={repoId} jobId={jobId} />
      </main>
    </>
  );
}
