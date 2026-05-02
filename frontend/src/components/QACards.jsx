import { motion } from "framer-motion";
import { Info } from "lucide-react";

const CARDS = [
  { key: "anti_slop", label: "Anti-slop", hint: "Distinct. Not generic AI-looking." },
  { key: "palette", label: "Palette", hint: "Cohesive, distinctive, accessible." },
  { key: "mobile", label: "Mobile", hint: "Flawless on small screens." },
  { key: "overall", label: "Overall", hint: "Gestalt quality." },
];

export function QACards({ title, scores }) {
  const s = scores || { anti_slop: 0, palette: 0, mobile: 0, overall: 0, notes: "" };
  return (
    <div className="panel p-5" data-testid="qa-panel">
      <div className="flex items-center justify-between mb-4">
        <div>
          <div className="text-[11px] uppercase tracking-[0.18em] text-white/45">QA Rubric</div>
          <div className="mt-1 text-lg font-semibold tracking-tight">{title}</div>
        </div>
        <OverallPill overall={s.overall} />
      </div>
      <div className="grid grid-cols-2 gap-3">
        {CARDS.map((c) => (
          <Scorecard key={c.key} label={c.label} hint={c.hint} score={s[c.key] ?? 0} slug={c.key} />
        ))}
      </div>
      {s.notes ? (
        <div
          className="mt-4 rounded-xl border border-white/10 bg-white/[0.02] p-3 text-[12.5px] text-white/75 whitespace-pre-wrap leading-relaxed"
          data-testid="qa-notes"
        >
          <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.16em] text-white/45 mb-1">
            <Info size={11} /> Reviewer notes
          </div>
          {s.notes}
        </div>
      ) : null}
    </div>
  );
}

function OverallPill({ overall }) {
  const color = overall >= 85 ? "var(--teal)" : overall >= 70 ? "#FFCC66" : "#FF5A7A";
  return (
    <div className="flex items-center gap-2 chip" style={{ color }} data-testid="qa-overall-pill">
      <span className="size-1.5 rounded-full" style={{ background: color }} />
      Overall {overall}/100
    </div>
  );
}

function Scorecard({ label, hint, score, slug }) {
  const color = score >= 85 ? "var(--teal)" : score >= 70 ? "#FFCC66" : "#FF5A7A";
  const pct = Math.max(0, Math.min(100, Number(score) || 0));
  return (
    <div
      className="relative rounded-xl border border-white/10 bg-white/[0.02] p-4 group"
      data-testid={`qa-scorecard-${slug}`}
    >
      <div className="flex items-center justify-between">
        <div className="text-[11px] uppercase tracking-[0.18em] text-white/55">{label}</div>
        <div
          className="text-[10px] uppercase tracking-[0.16em]"
          style={{ color }}
          data-testid={`qa-scorecard-${slug}-status`}
        >
          {score >= 85 ? "Pass" : score >= 70 ? "Warn" : score > 0 ? "Fail" : "—"}
        </div>
      </div>
      <div className="mt-2 flex items-end gap-1">
        <div
          className="font-display text-4xl font-semibold tracking-tight tabular-nums"
          data-testid={`qa-scorecard-${slug}-score`}
          style={{ color }}
        >
          {score || 0}
        </div>
        <div className="text-[11px] text-white/40 mb-1">/100</div>
      </div>
      <div className="mt-3 h-1 rounded-full bg-white/5 overflow-hidden">
        <motion.div
          className="h-full"
          style={{ background: color }}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
        />
      </div>
      <div className="mt-2 text-[11px] text-white/40">{hint}</div>
    </div>
  );
}
