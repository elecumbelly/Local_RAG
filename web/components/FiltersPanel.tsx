"use client";

import { useEffect, useState } from "react";
import { listCollections } from "@/lib/api";

type Props = {
  selected: string[];
  onChange: (values: string[]) => void;
};

export default function FiltersPanel({ selected, onChange }: Props) {
  const [collections, setCollections] = useState<string[]>([]);

  useEffect(() => {
    async function load() {
      try {
        const cols = await listCollections();
        setCollections(cols.map((c) => c.name));
        if (!selected.length) {
          onChange(cols.map((c) => c.name));
        }
      } catch {
        // keep empty on failure
      }
    }
    load();
  }, []);

  const toggle = (col: string) => {
    if (selected.includes(col)) {
      onChange(selected.filter((c) => c !== col));
    } else {
      onChange([...selected, col]);
    }
  };

  if (!collections.length) {
    return <div className="text-sm text-muted-foreground">No collections available.</div>;
  }

  return (
    <div className="flex gap-1 flex-wrap">
      {collections.map((c) => (
        <button
          key={c}
          onClick={() => toggle(c)}
          className={`px-3 py-1 text-sm font-medium rounded-full transition-all ${
            selected.includes(c)
              ? "bg-primary text-primary-foreground"
              : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
          }`}
        >
          {c}
        </button>
      ))}
    </div>
  );
}
