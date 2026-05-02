import { motion } from "framer-motion";
import { STAGES } from "@/lib/stages";
import { Check, Loader2, AlertTriangle } from "lucide-react";

export function PipelineStepper({ steps }) {
  const byKey = Object.fromEntries((steps || []).map((s) => [s.key, s]));
  const done = (steps || []).filter((s) => s.status === "done").length;
  const total = STAGES.length;
  const percent = Math.round((done / total) * 100);
  return (
    <div className="panel p-5 relative overflow-hidden" data-testid="pipeline-stepper">
      <div className="flex items-center justify-between mb-4">
        <div>
          <div className="text-[11px] uppercase tracking-[0.18em] text-white/45">
            Pipeline
          </div>
          <div className="mt-1 text-lg font-semibold tracking-tight">
            Transformation progress
          </div>
        </div>
        <div className="text-right">
          <div
            className="text-3xl font-semibold tabular-nums tracking-tight"
            data-testid="pipeline-overall-progress"
          >
            {percent}%
          </div>
          <div className="text-[11px] text-white/50">
            {done}/{total} stages
          </div>
        </div>
      </div>
      <div className="h-1.5 rounded-full bg-white/5 overflow-hidden mb-5">
        <motion.div
          className="h-full bg-[var(--teal)]"
          initial={{ width: 0 }}
          animate={{ width: `${percent}%` }}
          transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
        />
      </div>
      <ol className="relative">
        <span className="absolute left-[9px] top-1 bottom-1 w-px bg-white/10" aria-hidden />
        {STAGES.map((stage, i) => {
          const s = byKey[stage.key] || { status: "pending" };
          return (
            <li
              key={stage.key}
              className="relative pl-8 pb-5 last:pb-0"
              data-testid={`pipeline-step-${stage.key}`}
            >
              <StepDot status={s.status} />
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="text-[13px] font-medium text-white/90 tracking-tight">
                    {String(i + 1).padStart(2, "0")} &middot; {stage.label}
                  </div>
                  <div className="text-xs text-white/55 mt-0.5">{stage.desc}</div>
                  {s.message && (
                    <div className="text-[11px] text-white/70 mt-1 mono">{s.message}</div>
                  )}
                </div>
                <StatusBadge status={s.status} />
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}

function StepDot({ status }) {
  if (status === "running") {
    return (
      <motion.span
        className="absolute left-[3px] top-[2px] size-[13px] rounded-full bg-[var(--teal)] shadow-[0_0_0_4px_rgba(45,227,198,0.18)]"
        animate={{ scale: [1, 1.1, 1] }}
        transition={{ duration: 1.6, repeat: Infinity, ease: "easeInOut" }}
      />
    );
  }
  if (status === "done") {
    return (
      <span className="absolute left-[3px] top-[2px] size-[13px] rounded-full bg-[var(--teal)]/20 border border-[var(--teal)] grid place-items-center">
        <Check size={9} className="text-[var(--teal)]" strokeWidth={3} />
      </span>
    );
  }
  if (status === "error") {
    return (
      <span className="absolute left-[3px] top-[2px] size-[13px] rounded-full bg-rose-500/30 border border-rose-400 grid place-items-center">
        <AlertTriangle size={8} className="text-rose-300" />
      </span>
    );
  }
  return (
    <span className="absolute left-[3px] top-[2px] size-[13px] rounded-full border border-white/20 bg-transparent" />
  );
}

function StatusBadge({ status }) {
  const map = {
    pending: { text: "Pending", cls: "text-white/45" },
    running: { text: "Running", cls: "text-[var(--teal)]" },
    done: { text: "Complete", cls: "text-[var(--teal)]" },
    error: { text: "Error", cls: "text-rose-400" },
  };
  const m = map[status] || map.pending;
  return (
    <span
      className={`text-[10px] uppercase tracking-[0.18em] font-medium ${m.cls}`}
      data-testid="pipeline-step-status"
    >
      {status === "running" && (
        <Loader2 size={10} className="inline mr-1 animate-spin align-[-1px]" />
      )}
      {m.text}
    </span>
  );
}
