import { motion } from "framer-motion";
import { Info, AlertTriangle, UserX } from "lucide-react";

// 8-metric $25k rubric (plus overall)
const CARDS_25K = [
  { key: "distinct_design", label: "Distinct Design", hint: "Clear POV, not generic." },
  { key: "typography_hierarchy", label: "Typography", hint: "Scale, pairing, rhythm." },
  { key: "palette_cohesion", label: "Palette", hint: "One brand. Accessible." },
  { key: "spacing_rhythm", label: "Spacing", hint: "Generous whitespace." },
  { key: "no_overlap", label: "No Overlap", hint: "Zero clipping / collisions." },
  { key: "no_humans_in_images", label: "No Humans", hint: "Images: zero people/faces." },
  { key: "copy_quality", label: "Copy", hint: "Concrete, no AI-slop." },
  { key: "premium_feel", label: "Premium Feel", hint: "$25k agency craft." },
];

// Legacy 4-metric rubric (used only for qa_original)
const CARDS_LEGACY = [
  { key: "anti_slop", label: "Anti-slop", hint: "Distinct. Not generic." },
  { key: "palette", label: "Palette", hint: "Cohesive, accessible." },
  { key: "mobile", label: "Mobile", hint: "Flawless on small screens." },
  { key: "overall", label: "Overall", hint: "Gestalt quality." },
];

export function QACards({ title, scores, variant = "auto" }) {
  const is25k =
    variant === "25k" ||
    (variant === "auto" && scores && "distinct_design" in scores);
  const cards = is25k ? CARDS_25K : CARDS_LEGACY;
  const s = scores || {};
  const hasData = (s.overall || 0) > 0;
  const overlaps = Array.isArray(s.overlap_regions) ? s.overlap_regions : [];
  const humans = Array.isArray(s.human_detections) ? s.human_detections : [];

  return (
    <div className="panel p-5" data-testid="qa-panel">
      <div className="flex items-center justify-between mb-4">
        <div>
          <div className="text-[11px] uppercase tracking-[0.18em] text-white/45">
            {is25k ? "$25k Rubric" : "QA Rubric"}
          </div>
          <div className="mt-1 text-lg font-semibold tracking-tight">{title}</div>
        </div>
        <OverallPill overall={s.overall || 0} />
      </div>
      <div className={`grid gap-3 ${is25k ? "grid-cols-2 md:grid-cols-4" : "grid-cols-2"}`}>
        {cards.map((c) => (
          <Scorecard
            key={c.key}
            label={c.label}
            hint={c.hint}
            score={s[c.key] ?? 0}
            slug={c.key}
            compact={is25k}
          />
        ))}
      </div>

      {/* Overall as its own "prominent" row for $25k view */}
      {is25k && (
        <div className="mt-4 rounded-xl border border-white/10 bg-white/[0.02] p-4 flex items-center justify-between">
          <div>
            <div className="text-[11px] uppercase tracking-[0.18em] text-white/55">Overall</div>
            <div className="text-[12px] text-white/50 mt-0.5">Gestalt quality — would a $25k agency ship this?</div>
          </div>
          <div
            className="font-display text-4xl font-semibold tracking-tight tabular-nums"
            style={{ color: colorFor(s.overall || 0) }}
            data-testid="qa-overall-large"
          >
            {s.overall || 0}
            <span className="text-white/40 text-sm ml-1">/100</span>
          </div>
        </div>
      )}

      {hasData && overlaps.length > 0 && (
        <DetectionList
          icon={<AlertTriangle size={12} />}
          label={`Overlap regions (${overlaps.length})`}
          items={overlaps}
          tone="warn"
          testId="qa-overlap-list"
        />
      )}
      {hasData && humans.length > 0 && (
        <DetectionList
          icon={<UserX size={12} />}
          label={`Humans detected (${humans.length}) — image regen on retry`}
          items={humans}
          tone="error"
          testId="qa-humans-list"
        />
      )}

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

function DetectionList({ icon, label, items, tone, testId }) {
  const color = tone === "error" ? "#FF5A7A" : "#FFCC66";
  return (
    <div
      className="mt-3 rounded-xl border px-3 py-2 text-[12px]"
      style={{
        borderColor: `${color}33`,
        background: `${color}0D`,
        color,
      }}
      data-testid={testId}
    >
      <div className="flex items-center gap-1.5 font-medium">
        {icon}
        {label}
      </div>
      <ul className="mt-1 space-y-0.5 text-white/65">
        {items.slice(0, 6).map((b, i) => (
          <li key={i} className="font-mono text-[11px]">
            · {b.label || "unlabeled"} @ (
            {(b.x || 0).toFixed?.(2) ?? b.x},
            {(b.y || 0).toFixed?.(2) ?? b.y}) size (
            {(b.w || 0).toFixed?.(2) ?? b.w}×{(b.h || 0).toFixed?.(2) ?? b.h})
          </li>
        ))}
      </ul>
    </div>
  );
}

function colorFor(v) {
  return v >= 85 ? "var(--teal)" : v >= 70 ? "#FFCC66" : v > 0 ? "#FF5A7A" : "rgba(255,255,255,0.4)";
}

function OverallPill({ overall }) {
  const color = colorFor(overall);
  return (
    <div className="flex items-center gap-2 chip" style={{ color }} data-testid="qa-overall-pill">
      <span className="size-1.5 rounded-full" style={{ background: color }} />
      Overall {overall}/100
    </div>
  );
}

function Scorecard({ label, hint, score, slug, compact }) {
  const color = colorFor(score);
  const pct = Math.max(0, Math.min(100, Number(score) || 0));
  return (
    <div
      className="relative rounded-xl border border-white/10 bg-white/[0.02] p-4 group"
      data-testid={`qa-scorecard-${slug}`}
    >
      <div className="flex items-center justify-between">
        <div className="text-[11px] uppercase tracking-[0.16em] text-white/55 truncate">
          {label}
        </div>
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
          className={`font-display font-semibold tracking-tight tabular-nums ${compact ? "text-3xl" : "text-4xl"}`}
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
      {!compact && <div className="mt-2 text-[11px] text-white/40">{hint}</div>}
    </div>
  );
}
