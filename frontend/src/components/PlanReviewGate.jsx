import { useEffect, useMemo, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Check, Edit3, Timer, X, AlertCircle, Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { reviewPlan } from "@/lib/api";

/**
 * Renders when job.status === "awaiting_review".
 * Shows a 120-second countdown + editable plan (brand, palette, pages).
 * If the user does nothing, the backend auto-continues when the timer hits 0.
 */
export function PlanReviewGate({ job }) {
  const deadline = job?.review_deadline
    ? new Date(job.review_deadline).getTime()
    : null;
  const [now, setNow] = useState(() => Date.now());
  const [busy, setBusy] = useState(false);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(() => buildDraft(job));

  // Rebuild draft when the job object first loads
  const lastJobId = useRef(job?.id);
  useEffect(() => {
    if (job?.id !== lastJobId.current) {
      setDraft(buildDraft(job));
      lastJobId.current = job?.id;
    }
  }, [job]);

  // Tick every 250ms for a smooth countdown
  useEffect(() => {
    if (!deadline) return;
    const t = setInterval(() => setNow(Date.now()), 250);
    return () => clearInterval(t);
  }, [deadline]);

  const remainingMs = deadline ? Math.max(0, deadline - now) : 0;
  const totalMs = 120_000;
  const percent = Math.max(
    0,
    Math.min(100, Math.round((remainingMs / totalMs) * 100))
  );
  const secondsLeft = Math.ceil(remainingMs / 1000);
  const ringColor =
    percent > 50 ? "var(--teal)" : percent > 20 ? "#FFCC66" : "#FF5A7A";

  const submit = async (action) => {
    if (!job?.id || busy) return;
    setBusy(true);
    try {
      const payload =
        action === "edit" ? buildPlanFromDraft(draft) : undefined;
      await reviewPlan(job.id, action, payload);
      toast.success(
        action === "accept"
          ? "Plan accepted — building site now"
          : action === "edit"
          ? "Edits saved — building site now"
          : "Skipped — pipeline continues"
      );
    } catch (e) {
      toast.error(
        e?.response?.data?.detail || `Failed to ${action} the plan`
      );
    } finally {
      setBusy(false);
    }
  };

  if (job?.status !== "awaiting_review") return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 8 }}
      className="panel p-5 border-[var(--teal)]/30 bg-[var(--teal)]/[0.04] relative overflow-hidden"
      data-testid="plan-review-gate"
    >
      <div className="flex items-start justify-between gap-4 mb-5">
        <div className="flex items-center gap-3">
          <div className="relative size-14 shrink-0">
            <svg viewBox="0 0 48 48" className="size-14 -rotate-90">
              <circle
                cx="24"
                cy="24"
                r="20"
                stroke="rgba(255,255,255,0.08)"
                strokeWidth="4"
                fill="none"
              />
              <motion.circle
                cx="24"
                cy="24"
                r="20"
                stroke={ringColor}
                strokeWidth="4"
                strokeLinecap="round"
                fill="none"
                strokeDasharray={2 * Math.PI * 20}
                animate={{
                  strokeDashoffset:
                    2 * Math.PI * 20 * (1 - percent / 100),
                }}
                transition={{ duration: 0.3, ease: "linear" }}
              />
            </svg>
            <div
              className="absolute inset-0 grid place-items-center text-[13px] font-semibold tabular-nums"
              style={{ color: ringColor }}
              data-testid="plan-review-countdown"
            >
              {secondsLeft}s
            </div>
          </div>
          <div>
            <div className="text-[11px] uppercase tracking-[0.18em] text-[var(--teal)]">
              <Timer size={11} className="inline mr-1 align-[-1px]" />
              Review window
            </div>
            <div className="mt-1 text-lg font-semibold tracking-tight">
              Review the plan, or let it run
            </div>
            <div className="text-[12px] text-white/55">
              You have 2 minutes to edit brand, palette, and pages. After that the
              pipeline auto-continues with the current plan.
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {!editing && (
            <button
              className="btn-ghost h-9 text-xs"
              onClick={() => setEditing(true)}
              data-testid="plan-review-edit"
            >
              <Edit3 size={12} /> Edit
            </button>
          )}
          {editing && (
            <button
              className="btn-ghost h-9 text-xs"
              onClick={() => {
                setEditing(false);
                setDraft(buildDraft(job));
              }}
              data-testid="plan-review-cancel-edit"
            >
              <X size={12} /> Cancel
            </button>
          )}
          <button
            className="btn-primary h-9 text-xs"
            disabled={busy}
            onClick={() => submit(editing ? "edit" : "accept")}
            data-testid="plan-review-accept"
          >
            <Check size={12} />
            {editing ? "Save & continue" : "Accept & continue"}
          </button>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <BrandPaletteCard draft={draft} setDraft={setDraft} editing={editing} />
        <PagesCard draft={draft} setDraft={setDraft} editing={editing} />
      </div>

      <div className="mt-4 text-[11px] text-white/45 flex items-center gap-1.5">
        <AlertCircle size={11} /> Tip: if you do nothing, we auto-accept this plan
        and continue to Generate.
      </div>
    </motion.div>
  );
}

// --- draft helpers ---------------------------------------------------------

function buildDraft(job) {
  if (!job) return { brand: {}, design: {}, pages: [], nav: [] };
  return {
    niche: job.niche || "",
    brand: {
      name: (job.brand && job.brand.name) || "",
      tagline: (job.brand && job.brand.tagline) || "",
      voice: (job.brand && job.brand.voice) || "",
    },
    design: {
      primary: (job.design_tokens && job.design_tokens.primary) || "#2DE3C6",
      accent: (job.design_tokens && job.design_tokens.accent) || "#FFB86B",
      bg: (job.design_tokens && job.design_tokens.bg) || "#070A0E",
      fg: (job.design_tokens && job.design_tokens.fg) || "#EAF0FF",
      font_heading:
        (job.design_tokens && job.design_tokens.font_heading) || "Space Grotesk",
      font_body:
        (job.design_tokens && job.design_tokens.font_body) || "Inter",
    },
    pages: (job.pages_plan || []).map((p) => ({
      route: p.route || "/",
      title: p.title || "",
      purpose: p.purpose || "",
      sectionCount: (p.sections || []).length,
      _raw: p,
    })),
    nav: job.nav_plan || [],
  };
}

function buildPlanFromDraft(draft) {
  return {
    niche: draft.niche || undefined,
    brand: draft.brand,
    design: draft.design,
    pages: draft.pages.map((p) => {
      // Preserve original sections when present, otherwise supply a minimal stub
      const raw = p._raw || {};
      return {
        ...raw,
        route: p.route,
        title: p.title,
        purpose: p.purpose,
      };
    }),
    nav: draft.nav,
  };
}

function BrandPaletteCard({ draft, setDraft, editing }) {
  const swatches = [
    { key: "primary", label: "Primary" },
    { key: "accent", label: "Accent" },
    { key: "bg", label: "Background" },
    { key: "fg", label: "Foreground" },
  ];
  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.02] p-4">
      <div className="text-[11px] uppercase tracking-[0.18em] text-white/45 mb-3">
        Brand & Palette
      </div>
      <div className="space-y-2.5">
        <LabeledInput
          label="Brand name"
          value={draft.brand.name}
          disabled={!editing}
          onChange={(v) =>
            setDraft((d) => ({ ...d, brand: { ...d.brand, name: v } }))
          }
          testId="plan-review-brand-name"
        />
        <LabeledInput
          label="Tagline"
          value={draft.brand.tagline}
          disabled={!editing}
          onChange={(v) =>
            setDraft((d) => ({ ...d, brand: { ...d.brand, tagline: v } }))
          }
          testId="plan-review-brand-tagline"
        />
      </div>
      <div className="mt-4 grid grid-cols-4 gap-2">
        {swatches.map((s) => (
          <SwatchPicker
            key={s.key}
            label={s.label}
            value={draft.design[s.key] || "#000000"}
            disabled={!editing}
            onChange={(v) =>
              setDraft((d) => ({ ...d, design: { ...d.design, [s.key]: v } }))
            }
            testId={`plan-review-swatch-${s.key}`}
          />
        ))}
      </div>
    </div>
  );
}

function PagesCard({ draft, setDraft, editing }) {
  const addPage = () =>
    setDraft((d) => ({
      ...d,
      pages: [
        ...d.pages,
        { route: "/new-page", title: "New page", purpose: "", sectionCount: 3 },
      ],
    }));
  const removePage = (idx) =>
    setDraft((d) => ({ ...d, pages: d.pages.filter((_, i) => i !== idx) }));
  const updatePage = (idx, patch) =>
    setDraft((d) => ({
      ...d,
      pages: d.pages.map((p, i) => (i === idx ? { ...p, ...patch } : p)),
    }));

  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.02] p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="text-[11px] uppercase tracking-[0.18em] text-white/45">
          Pages ({draft.pages.length})
        </div>
        {editing && (
          <button
            className="btn-ghost h-7 text-[11px]"
            onClick={addPage}
            data-testid="plan-review-add-page"
          >
            <Plus size={11} /> Add
          </button>
        )}
      </div>
      <div className="space-y-2 max-h-[260px] overflow-y-auto pr-1">
        <AnimatePresence initial={false}>
          {draft.pages.map((p, i) => (
            <motion.div
              key={`${i}-${p.route}`}
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              className="rounded-lg border border-white/5 bg-black/20 px-3 py-2 flex items-center gap-2"
              data-testid={`plan-review-page-row-${i}`}
            >
              <div className="font-mono text-[11px] text-white/50 w-14 shrink-0 truncate">
                {p.route}
              </div>
              <input
                value={p.title}
                disabled={!editing}
                onChange={(e) => updatePage(i, { title: e.target.value })}
                className="flex-1 bg-transparent text-[13px] outline-none disabled:opacity-80"
                data-testid={`plan-review-page-title-${i}`}
              />
              <span className="chip text-[10px]">
                {p.sectionCount} sections
              </span>
              {editing && draft.pages.length > 1 && (
                <button
                  onClick={() => removePage(i)}
                  className="text-white/30 hover:text-rose-300 transition-colors"
                  data-testid={`plan-review-page-remove-${i}`}
                >
                  <Trash2 size={12} />
                </button>
              )}
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}

function LabeledInput({ label, value, onChange, disabled, testId }) {
  return (
    <label className="block">
      <div className="text-[10px] uppercase tracking-[0.16em] text-white/40 mb-1">
        {label}
      </div>
      <input
        value={value || ""}
        disabled={disabled}
        onChange={(e) => onChange?.(e.target.value)}
        className="w-full bg-black/20 border border-white/10 rounded-md px-2.5 h-9 text-[13px] outline-none focus:border-[var(--teal)]/50 disabled:opacity-70"
        data-testid={testId}
      />
    </label>
  );
}

function SwatchPicker({ label, value, onChange, disabled, testId }) {
  return (
    <label className="flex flex-col items-start gap-1" data-testid={testId}>
      <div className="text-[10px] uppercase tracking-[0.16em] text-white/40">
        {label}
      </div>
      <div className="flex items-center gap-1.5 w-full">
        <span
          className="size-7 rounded-md border border-white/10 shrink-0"
          style={{ background: value }}
        />
        <input
          type="text"
          value={value || ""}
          disabled={disabled}
          onChange={(e) => onChange?.(e.target.value)}
          className="flex-1 min-w-0 bg-black/20 border border-white/10 rounded-md px-2 h-7 text-[11px] font-mono outline-none focus:border-[var(--teal)]/50 disabled:opacity-70"
        />
      </div>
    </label>
  );
}
