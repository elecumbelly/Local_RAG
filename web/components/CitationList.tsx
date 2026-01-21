"use client";

import { apiBase } from "@/lib/api";
import { toast } from "sonner";

type Citation = { document_id?: number; path: string; page: number; score: number; content: string };

export default function CitationList({ citations }: { citations: Citation[] }) {
  const handleOpen = async (id: number, page: number) => {
    const url = `${apiBase}/documents/${id}/file`;
    try {
      const res = await fetch(url);
      if (!res.ok) throw new Error("Failed to fetch file");
      
      const blob = await res.blob();
      const objectUrl = URL.createObjectURL(blob);
      window.open(`${objectUrl}#page=${page}`, "_blank", "noopener,noreferrer");
    } catch (err) {
      toast.error("Could not open document");
    }
  };

  return (
    <div className="space-y-3">
      {citations.map((c, idx) => (
        <div key={idx} className="card p-4 card-hover">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs font-mono text-primary">{c.path.split('/').pop()}</span>
              <span className="text-xs text-muted-foreground">page {c.page}</span>
              <span className="text-xs text-muted-foreground/50">score: {c.score.toFixed(3)}</span>
            </div>
            {c.document_id && (
              <button
                onClick={() => handleOpen(c.document_id!, c.page)}
                className="text-xs text-muted-foreground hover:text-primary transition-colors"
              >
                Open →
              </button>
            )}
          </div>
          <div className="text-sm text-muted-foreground leading-relaxed">
            {c.content.slice(0, 400)}
            {c.content.length > 400 && "..."}
          </div>
        </div>
      ))}
      {!citations.length && <div className="text-sm text-muted-foreground">No citations.</div>}
    </div>
  );
}
