"use client";

import { Sparkles } from "lucide-react";
import { useEffect, useState } from "react";
import { LiquidGlassCard } from "@/components/liquid-glass-card";
import { RagBadge } from "@/components/dashboard/rag-badge";
import { StoreSelect } from "@/components/dashboard/store-select";
import { generateNarrative, getNarrative, type NarrativeResponse } from "@/lib/api";

const dateFmt = new Intl.DateTimeFormat("en-US", { dateStyle: "medium", timeStyle: "short" });

type Result = { key: string; narrative: NarrativeResponse | null };

export function NarrativeSection({ stores }: { stores: string[] }) {
  const [storeId, setStoreId] = useState(stores[0] ?? "");
  const [result, setResult] = useState<Result | null>(null);
  const [generating, setGenerating] = useState(false);
  const [generateError, setGenerateError] = useState<string | null>(null);
  const loading = result?.key !== storeId;
  const narrative = loading ? null : (result?.narrative ?? null);

  useEffect(() => {
    if (!storeId) return;
    let cancelled = false;
    getNarrative(storeId)
      .catch(() => null)
      .then((n) => {
        if (!cancelled) setResult({ key: storeId, narrative: n });
      });
    return () => {
      cancelled = true;
    };
  }, [storeId]);

  async function handleGenerate() {
    setGenerating(true);
    setGenerateError(null);
    try {
      const fresh = await generateNarrative(storeId);
      setResult({ key: storeId, narrative: fresh });
    } catch (err) {
      setGenerateError(err instanceof Error ? err.message : "Generation failed.");
    } finally {
      setGenerating(false);
    }
  }

  return (
    <LiquidGlassCard className="liquid-glass-interactive min-w-0 px-6 py-6 sm:px-8 sm:py-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <h2 className="text-base font-medium text-neutral-200">AI narrative browser</h2>
        <div className="flex flex-wrap items-end gap-3">
          <StoreSelect stores={stores} value={storeId} onChange={setStoreId} label="Store" />
          <button
            onClick={handleGenerate}
            disabled={generating || !storeId}
            className="inline-flex items-center gap-1.5 rounded-full bg-white px-4 py-2.5 text-xs font-medium text-black transition-colors hover:bg-neutral-200 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Sparkles className="size-3.5" aria-hidden />
            {generating ? "Generating via Ollama…" : "Generate AI analysis"}
          </button>
        </div>
      </div>
      <div className="mt-4">
        {loading && <p className="text-sm text-neutral-500">Loading…</p>}
        {!loading && narrative ? (
          <>
            <p className="text-base leading-relaxed text-neutral-200">{narrative.summary}</p>
            <p className="mt-3 text-xs text-neutral-500">Generated {dateFmt.format(new Date(narrative.generated_at))}</p>
            {narrative.retrieved_sources && <RagBadge sources={narrative.retrieved_sources} />}
          </>
        ) : (
          !loading && <p className="text-sm text-neutral-500">No narrative generated yet for {storeId || "this store"}.</p>
        )}
        {generateError && <p className="mt-3 text-xs text-red-400">{generateError}</p>}
      </div>
    </LiquidGlassCard>
  );
}
