"use client";

import { useEffect, useState } from "react";
import { listOllamaModels } from "@/lib/api";

type ModelSettings = {
  temperature: number;
  top_p: number;
  max_tokens: number;
};

type Props = {
  selected: string | undefined;
  settings: ModelSettings;
  onModelChange: (model: string | undefined) => void;
  onSettingsChange: (settings: ModelSettings) => void;
};

export default function ModelSelector({ selected, settings, onModelChange, onSettingsChange }: Props) {
  const [models, setModels] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdvanced, setShowAdvanced] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const ollamaModels = await listOllamaModels();
        setModels(ollamaModels.map((m) => m.name));
        if (!selected && ollamaModels.length > 0) {
          onModelChange(ollamaModels[0].name);
        }
      } catch {
        setLoading(false);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const updateSetting = <K extends keyof ModelSettings>(key: K, value: ModelSettings[K]) => {
    onSettingsChange({ ...settings, [key]: value });
  };

  if (loading) {
    return <div className="text-sm text-muted-foreground">Loading models...</div>;
  }

  if (!models.length) {
    return <div className="text-sm text-muted-foreground">No Ollama models available.</div>;
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-3">
        <select
          id="model-select"
          value={selected || ""}
          onChange={(e) => onModelChange(e.target.value || undefined)}
          className="input px-3 py-1.5 text-sm font-mono"
        >
          {models.map((model) => (
            <option key={model} value={model}>
              {model}
            </option>
          ))}
        </select>
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="text-xs text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1"
        >
          <span className={showAdvanced ? "rotate-90" : ""}>▶</span>
          Advanced
        </button>
      </div>

      {showAdvanced && (
        <div className="card p-4 space-y-4 animate-slide-up">
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-xs text-muted-foreground mb-2">Temperature</label>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={settings.temperature}
                onChange={(e) => updateSetting("temperature", parseFloat(e.target.value))}
                className="w-full accent-primary"
              />
              <div className="text-xs text-right mt-1 font-mono">{settings.temperature.toFixed(1)}</div>
            </div>
            <div>
              <label className="block text-xs text-muted-foreground mb-2">Top P</label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={settings.top_p}
                onChange={(e) => updateSetting("top_p", parseFloat(e.target.value))}
                className="w-full accent-primary"
              />
              <div className="text-xs text-right mt-1 font-mono">{settings.top_p.toFixed(2)}</div>
            </div>
            <div>
              <label className="block text-xs text-muted-foreground mb-2">Max Tokens</label>
              <input
                type="number"
                min="100"
                max="32000"
                step="100"
                value={settings.max_tokens}
                onChange={(e) => updateSetting("max_tokens", parseInt(e.target.value))}
                className="input px-2 py-1 text-sm font-mono w-full"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
