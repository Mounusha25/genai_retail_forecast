import { BookOpen } from "lucide-react";

export function RagBadge({ sources }: { sources: string[] }) {
  if (sources.length === 0) return null;
  const uniqueFiles = [...new Set(sources.map((s) => s.split("/").pop() ?? s))];

  return (
    <div className="mt-3 flex items-center gap-1.5 text-xs text-neutral-500">
      <BookOpen className="size-3.5" aria-hidden />
      <span>
        RAG-grounded — {sources.length} retrieved passage{sources.length === 1 ? "" : "s"} from {uniqueFiles.join(", ")}
      </span>
    </div>
  );
}
