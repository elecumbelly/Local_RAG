"use client";

import { useEffect, useState } from "react";
import { apiBase, deleteDocument, fetchDocuments, updateTags, ingest } from "@/lib/api";
import { toast } from "sonner";
import TagEditor from "./TagEditor";

type Doc = {
  id: number;
  path: string;
  tags: string[];
  status: string;
  ocr_applied: boolean;
  processed_path?: string | null;
  extracted_chars: number;
  empty_page_ratio: number;
  quality?: { doc?: { extracted_chars: number; empty_page_ratio: number }; pages?: any[] };
  collection: string;
};

function SkeletonCard() {
  return (
    <div className="card p-4 animate-pulse">
      <div className="flex justify-between items-start">
        <div className="space-y-2 flex-1">
          <div className="h-4 bg-muted rounded w-3/4" />
          <div className="h-3 bg-muted rounded w-full" />
        </div>
        <div className="flex gap-2">
          <div className="h-8 w-20 bg-muted rounded" />
          <div className="h-8 w-16 bg-muted rounded" />
          <div className="h-8 w-28 bg-muted rounded" />
        </div>
      </div>
    </div>
  );
}

export default function DocumentTable() {
  const [docs, setDocs] = useState<Doc[]>([]);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    try {
      const data = await fetchDocuments({});
      setDocs(data);
    } catch (err) {
      console.error("Failed to load documents", err);
      toast.error("Failed to load documents");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const handleDelete = async (id: number) => {
    try {
      await deleteDocument(id);
      toast.success("Document deleted");
      load();
    } catch {
      toast.error("Failed to delete document");
    }
  };

  const handleOpen = async (id: number, processed: boolean) => {
    const url = `${apiBase}/documents/${id}/file${processed ? "?processed=true" : ""}`;
    const res = await fetch(url);
    if (!res.ok) {
      toast.error("Failed to open file");
      return;
    }
    const blob = await res.blob();
    const objectUrl = URL.createObjectURL(blob);
    window.open(objectUrl, "_blank", "noopener,noreferrer");
  };

  const handleReingest = async (collection: string) => {
    const promise = ingest(collection);
    toast.promise(promise, {
      loading: `Ingesting ${collection}...`,
      success: (data) => {
        load();
        return `Ingest Complete: ${data.processed} processed, ${data.skipped} skipped, ${data.failed} failed`;
      },
      error: "Ingest failed",
    });
  };

  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => <SkeletonCard key={i} />)}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {docs.map((d) => (
        <div key={d.id} className="card p-4 card-hover">
          <div className="flex justify-between items-start">
            <div>
              <div className="font-medium text-foreground">{d.path}</div>
              <div className="text-xs text-muted-foreground mt-1 flex items-center gap-4 flex-wrap">
                <span className="badge">{d.collection}</span>
                <span className={d.status === "ingested" ? "text-emerald-400" : "text-amber-400"}>
                  {d.status}
                </span>
                <span>OCR: {d.ocr_applied ? "Yes" : "No"}</span>
                <span>{d.extracted_chars.toLocaleString()} chars</span>
                <span>empty: {d.empty_page_ratio.toFixed(2)}</span>
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => handleOpen(d.id, Boolean(d.processed_path))}
                className="btn btn-outline text-xs"
              >
                Open PDF
              </button>
              <button
                onClick={() => handleDelete(d.id)}
                className="btn text-xs text-red-400 hover:text-red-300 hover:bg-red-950/30"
              >
                Delete
              </button>
              <button
                onClick={() => handleReingest(d.collection)}
                className="btn btn-primary text-xs"
              >
                Re-ingest
              </button>
            </div>
          </div>
          <div className="text-xs text-muted-foreground mt-3 flex items-center gap-2">
            <span>tags:</span>
            {d.tags.length > 0 ? (
              <div className="flex gap-1 flex-wrap">
                {d.tags.map((tag) => (
                  <span key={tag} className="badge badge-primary">{tag}</span>
                ))}
              </div>
            ) : (
              <span className="text-muted-foreground/50">none</span>
            )}
          </div>
          <TagEditor docId={d.id} initial={d.tags} onSaved={load} />
        </div>
      ))}
      {!docs.length && (
        <div className="card p-12 text-center border-dashed">
          <div className="text-muted-foreground text-sm">
            No documents found. Ingest a collection to see them here.
          </div>
        </div>
      )}
    </div>
  );
}
