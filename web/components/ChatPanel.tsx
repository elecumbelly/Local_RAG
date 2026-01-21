"use client";

import { useState } from "react";
import { apiBase } from "@/lib/api";
import { createParser, ParsedEvent, ReconnectInterval } from "eventsource-parser";
import { toast } from "sonner";
import FiltersPanel from "./FiltersPanel";
import CitationList from "./CitationList";
import ModelSelector from "./ModelSelector";

type Chunk = { document_id?: number; path: string; page: number; score: number; content: string };

type ModelSettings = {
  temperature: number;
  top_p: number;
  max_tokens: number;
};

export default function ChatPanel() {
  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState("");
  const [chunks, setChunks] = useState<Chunk[]>([]);
  const [loading, setLoading] = useState(false);
  const [collections, setCollections] = useState<string[]>(["library", "dev", "test"]);
  const [model, setModel] = useState<string | undefined>(undefined);
  const [settings, setSettings] = useState<ModelSettings>({ temperature: 0.7, top_p: 0.9, max_tokens: 4096 });

  const runChat = async () => {
    if (!query.trim()) return;

    setLoading(true);
    setAnswer("");
    setChunks([]);
    
    try {
      const res = await fetch(`${apiBase}/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query,
          collections,
          top_k: 8,
          model,
          provider: "ollama",
          temperature: settings.temperature,
          top_p: settings.top_p,
          max_tokens: settings.max_tokens,
        })
      });
      
      if (!res.ok) {
        const msg = await res.text();
        throw new Error(msg || "Chat request failed");
      }

      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      if (!reader) return;

      const parser = createParser((event: ParsedEvent | ReconnectInterval) => {
        if (event.type !== "event") return;
        const payload = event.data;
        if (payload === "[DONE]") {
          setLoading(false);
          return;
        }
        if (payload.startsWith("{")) {
          try {
            const parsed = JSON.parse(payload);
            if (parsed.chunks) {
              setChunks(parsed.chunks);
              return;
            }
          } catch {
            // ignore parse errors and continue streaming tokens
          }
        }
        setAnswer((prev) => prev + payload);
      });

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        parser.feed(chunk);
      }
    } catch (err: any) {
      toast.error("Query failed", { description: err.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-6 pt-24 pb-8 space-y-6">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <FiltersPanel selected={collections} onChange={setCollections} />
        <ModelSelector
          selected={model}
          settings={settings}
          onModelChange={setModel}
          onSettingsChange={setSettings}
        />
      </div>

      <div className="relative group">
        <div className="absolute inset-0 bg-gradient-to-r from-primary/20 to-accent/20 rounded-xl blur-xl opacity-0 group-focus-within:opacity-100 transition-opacity duration-500" />
        <div className="relative flex gap-2 card p-2">
          <input
            value={query}
            onKeyDown={(e) => e.key === "Enter" && runChat()}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a question about your corpus..."
            className="flex-1 input px-4 py-3 text-base"
          />
          <button
            onClick={runChat}
            disabled={loading || !query.trim()}
            className="btn btn-primary px-6 py-3"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Processing
              </span>
            ) : (
              "Ask"
            )}
          </button>
        </div>
      </div>

      <div className="card p-6 min-h-[200px] relative">
        {loading && !answer && (
          <div className="absolute inset-0 flex items-center justify-center card z-10">
            <div className="flex items-center gap-3 text-primary">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
              <span className="text-sm font-medium">Searching library</span>
              <span className="loading-dots" />
            </div>
          </div>
        )}
        <div className="whitespace-pre-wrap leading-relaxed text-foreground">
          {answer || (!loading && (
            <span className="text-muted-foreground italic">
              Responses will appear here with inline citations.
            </span>
          ))}
        </div>
      </div>

      {chunks.length > 0 && (
        <div className="animate-fade-in">
          <div className="text-sm font-medium text-muted-foreground mb-3 uppercase tracking-wider text-xs">
            Citations
          </div>
          <CitationList citations={chunks} />
        </div>
      )}
    </div>
  );
}
