import { useEffect, useMemo, useRef, useState } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";

export function LogStream({ logs }) {
  const [filter, setFilter] = useState("all");
  const [auto, setAuto] = useState(true);
  const ref = useRef(null);

  const filtered = useMemo(() => {
    if (filter === "all") return logs;
    if (filter === "warn") return logs.filter((l) => l.level === "warn" || l.level === "error");
    if (filter === "error") return logs.filter((l) => l.level === "error");
    return logs;
  }, [logs, filter]);

  useEffect(() => {
    if (!auto || !ref.current) return;
    const el = ref.current.querySelector("[data-radix-scroll-area-viewport]");
    if (el) el.scrollTop = el.scrollHeight;
  }, [filtered, auto]);

  return (
    <div className="panel relative overflow-hidden" data-testid="log-stream">
      <div className="flex items-center justify-between px-4 h-11 border-b border-white/5">
        <div className="flex items-center gap-3">
          <div className="text-[11px] uppercase tracking-[0.18em] text-white/45">
            Live log
          </div>
          <div className="flex items-center gap-1">
            {[
              { k: "all", label: "All" },
              { k: "warn", label: "Warn" },
              { k: "error", label: "Error" },
            ].map((t) => (
              <button
                key={t.k}
                onClick={() => setFilter(t.k)}
                data-testid={`log-filter-${t.k}`}
                className={`text-[11px] px-2 py-0.5 rounded-md transition-colors ${
                  filter === t.k
                    ? "bg-white/10 text-white"
                    : "text-white/55 hover:text-white hover:bg-white/5"
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>
        <label className="flex items-center gap-2 text-[11px] text-white/60 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={auto}
            onChange={(e) => setAuto(e.target.checked)}
            className="accent-[var(--teal)]"
            data-testid="log-autoscroll"
          />
          Auto-scroll
        </label>
      </div>
      <ScrollArea ref={ref} className="h-[320px]">
        <div className="px-4 py-3 font-mono text-[11.5px] leading-relaxed">
          {filtered.length === 0 ? (
            <div className="text-white/40">Waiting for events&hellip;</div>
          ) : (
            filtered.map((l, i) => (
              <div
                key={i}
                className={`flex gap-3 items-start py-[1.5px] log-${l.level || "info"}`}
                data-testid={`log-row-${i}`}
              >
                <span className="text-white/30 shrink-0 tabular-nums">
                  {l.ts ? l.ts.slice(11, 19) : ""}
                </span>
                {l.stage && (
                  <Badge
                    variant="secondary"
                    className="h-[18px] text-[10px] uppercase tracking-wider bg-white/[0.04] border border-white/10 text-white/70 shrink-0"
                  >
                    {l.stage}
                  </Badge>
                )}
                <span className="break-all">{l.message}</span>
              </div>
            ))
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
