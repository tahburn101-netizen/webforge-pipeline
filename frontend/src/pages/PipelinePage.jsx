import { useEffect, useRef, useState } from "react";
import { motion, useScroll, useTransform, useReducedMotion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { ArrowUpRight, Link as LinkIcon, Sparkles, Cpu, Shield, ChevronDown } from "lucide-react";
import { toast } from "sonner";
import { api, createJob } from "@/lib/api";
import { useJobStream } from "@/lib/useJobStream";
import { PipelineStepper } from "@/components/PipelineStepper";
import { LogStream } from "@/components/LogStream";
import { BeforeAfterViewer } from "@/components/BeforeAfterViewer";
import { QACards } from "@/components/QACards";
import { VideoUpload } from "@/components/VideoUpload";
import { DeployPanel } from "@/components/DeployPanel";

export default function PipelinePage() {
  const [url, setUrl] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [jobId, setJobId] = useState(null);
  const [referenceUrl, setReferenceUrl] = useState("");
  const [referenceOptions, setReferenceOptions] = useState([]);
  const navigate = useNavigate();
  const { job, logs } = useJobStream(jobId);

  useEffect(() => {
    api
      .get("/references")
      .then((r) => setReferenceOptions(r.data?.references || []))
      .catch(() => {});
  }, []);

  const heroRef = useRef(null);
  const reduce = useReducedMotion();
  const { scrollYProgress } = useScroll({
    target: heroRef,
    offset: ["start start", "end start"],
  });
  const progress = reduce ? { get: () => 0 } : scrollYProgress;
  const headingY = useTransform(progress, [0, 1], [0, -40]);
  const headingO = useTransform(progress, [0, 0.85], [1, 0.3]);
  const mediaScale = useTransform(progress, [0, 1], [1, 0.78]);
  const leftX = useTransform(progress, [0, 1], [0, -200]);
  const leftR = useTransform(progress, [0, 1], [0, -6]);
  const rightX = useTransform(progress, [0, 1], [0, 200]);
  const rightR = useTransform(progress, [0, 1], [0, 6]);

  useEffect(() => {
    if (!jobId) return;
    // reflect job id in URL fragment for copy-paste
    window.history.replaceState({}, "", `/#${jobId}`);
  }, [jobId]);

  const start = async () => {
    const clean = url.trim();
    if (!clean) {
      toast.error("Paste a website URL first");
      return;
    }
    setSubmitting(true);
    try {
      const j = await createJob({ input_url: clean });
      setJobId(j.id);
      toast.success("Transformation started");
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Failed to start job");
    } finally {
      setSubmitting(false);
    }
  };

  const onKeyDown = (e) => {
    if (e.key === "Enter") start();
  };

  return (
    <div className="min-h-[calc(100vh-56px)]">
      {/* Hero */}
      <section ref={heroRef} className="relative overflow-hidden">
        <div className="max-w-[1200px] mx-auto px-5 sm:px-8 pt-14 pb-14 sm:pt-20 sm:pb-20">
          <motion.div style={{ y: headingY, opacity: headingO }}>
            <div className="chip mb-5" data-testid="hero-chip">
              <Sparkles size={11} className="text-[var(--teal)]" /> AI Website Transformation Pipeline
            </div>
            <h1 className="font-display text-4xl sm:text-6xl lg:text-7xl font-semibold tracking-tight leading-[1.02] max-w-4xl">
              Transform any website into an{" "}
              <span className="text-[var(--teal)]">investor-ready</span> experience.
            </h1>
            <p className="mt-5 text-base sm:text-lg text-white/65 max-w-2xl">
              Paste a URL. We scrape, QA score it, reverse-engineer a beautiful reference,
              rebuild it as a multi-page Next.js site with a video hero + exploding scroll effect,
              QA-check desktop + mobile, and ship a public Vercel link.
            </p>
          </motion.div>

          {/* Command bar */}
          <motion.div
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1], delay: 0.05 }}
            className="mt-8"
          >
            <div
              className="rounded-2xl border border-white/10 bg-white/[0.04] backdrop-blur-md shadow-[var(--shadow-elev-1)] p-1.5 flex items-center gap-1 scanline"
              data-testid="command-bar"
            >
              <div className="pl-3 pr-1 text-white/45">
                <LinkIcon size={16} />
              </div>
              <input
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                onKeyDown={onKeyDown}
                placeholder="https://yourcompany.com"
                className="input-line flex-1"
                data-testid="website-url-input"
                autoFocus
                disabled={submitting}
              />
              <button
                className="btn-primary h-11 px-5"
                onClick={start}
                disabled={submitting}
                data-testid="transform-submit-button"
              >
                {submitting ? "Starting…" : "Transform"} <ArrowUpRight size={16} />
              </button>
            </div>
            {/* Reference picker */}
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <label className="text-[11px] uppercase tracking-[0.18em] text-white/40">
                Reference style
              </label>
              <div className="relative">
                <select
                  value={referenceUrl}
                  onChange={(e) => setReferenceUrl(e.target.value)}
                  data-testid="reference-select"
                  className="appearance-none bg-white/[0.04] border border-white/10 hover:bg-white/[0.06] transition-colors text-white/85 text-[12px] rounded-md py-1.5 pl-3 pr-8 outline-none focus:border-[var(--teal)]/40"
                >
                  <option value="">Auto-match niche</option>
                  {referenceOptions.map((r) => (
                    <option key={r.url} value={r.url}>
                      {r.name} — {r.vibe}
                    </option>
                  ))}
                </select>
                <ChevronDown
                  size={12}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-white/40 pointer-events-none"
                />
              </div>
              <span className="text-[11px] text-white/35">
                We extract its design tokens via skillui and apply your content.
              </span>
            </div>
            <div className="mt-3 flex items-center gap-5 text-[12px] text-white/50">
              <span className="inline-flex items-center gap-1.5"><Cpu size={12} /> Gemini 2.5 Pro vision</span>
              <span className="inline-flex items-center gap-1.5"><Shield size={12} /> QA-gated output</span>
              <span className="inline-flex items-center gap-1.5">
                <Sparkles size={12} /> Public Vercel URL
              </span>
            </div>
          </motion.div>
        </div>

        {/* Exploding preview strip */}
        <div className="relative pb-14">
          <motion.div
            style={{ scale: mediaScale }}
            className="relative mx-auto max-w-[1120px] aspect-[16/9] rounded-3xl overflow-hidden border border-white/10 bg-black glow-teal"
          >
            <div className="absolute inset-0" style={{
              background:
                "radial-gradient(900px 420px at 18% 10%, rgba(45,227,198,0.18), transparent 60%), radial-gradient(700px 360px at 82% 0%, rgba(255,184,107,0.14), transparent 55%), #0B1220"
            }} />
            <div className="absolute inset-0 grid place-items-center">
              <PreviewMockup />
            </div>
            <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent pointer-events-none" />
          </motion.div>
          <motion.div
            style={{ x: leftX, rotate: leftR }}
            className="hidden md:block absolute left-[6%] top-[15%] w-[260px] aspect-[4/3] rounded-2xl border border-white/10 bg-white/5 backdrop-blur glow-teal"
            aria-hidden
          />
          <motion.div
            style={{ x: rightX, rotate: rightR }}
            className="hidden md:block absolute right-[6%] bottom-[10%] w-[280px] aspect-[5/3] rounded-2xl border border-white/10 bg-white/5 backdrop-blur glow-teal"
            aria-hidden
          />
        </div>
      </section>

      {/* Pipeline workspace */}
      <section className="max-w-[1200px] mx-auto px-5 sm:px-8 pb-24">
        {!jobId ? (
          <EmptyWorkspace onPickSample={(s) => setUrl(s)} />
        ) : (
          <div className="grid lg:grid-cols-12 gap-5" data-testid="workspace">
            <div className="lg:col-span-5 space-y-5">
              <PipelineStepper steps={job?.steps || []} />
              <LogStream logs={logs} />
              <VideoUpload
                jobId={jobId}
                currentAssetId={job?.video_asset_id}
                onUploaded={() => toast.info("Video will be used on next iteration")}
              />
            </div>
            <div className="lg:col-span-7 space-y-5">
              <BeforeAfterViewer job={job} />
              <div className="grid md:grid-cols-2 gap-5">
                <QACards title="Original website" scores={job?.qa_original} />
                <QACards title="Generated website" scores={job?.qa_generated} />
              </div>
              <DeployPanel job={job} />
              {job?.status === "failed" && job?.error && (
                <div
                  className="panel p-4 border-rose-400/20 bg-rose-500/5 text-rose-200 text-sm"
                  data-testid="job-error"
                >
                  Pipeline error: {job.error}
                </div>
              )}
              <div className="flex justify-end">
                <button
                  className="btn-ghost"
                  onClick={() => navigate(`/jobs/${job?.id || jobId}`)}
                  data-testid="open-job-detail"
                >
                  Open full job detail <ArrowUpRight size={14} />
                </button>
              </div>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}

function EmptyWorkspace({ onPickSample }) {
  const samples = [
    "https://example.com",
    "https://craigslist.org",
    "https://news.ycombinator.com",
  ];
  return (
    <div className="grid md:grid-cols-3 gap-4" data-testid="empty-state">
      {[
        {
          title: "1 · Paste any URL",
          desc: "We capture desktop + mobile screenshots and extract every word.",
        },
        {
          title: "2 · Reverse-engineer a reference",
          desc: "skillui extracts the design system of a beautiful site in the same niche.",
        },
        {
          title: "3 · QA + Deploy",
          desc: "Multi-page Next.js, exploding video hero, QA-gated, public Vercel link.",
        },
      ].map((c) => (
        <div key={c.title} className="panel-soft p-5">
          <div className="text-[11px] uppercase tracking-[0.18em] text-[var(--teal)]">
            {c.title.split(" · ")[0]}
          </div>
          <div className="mt-1 text-[15px] font-semibold tracking-tight">
            {c.title.split(" · ")[1]}
          </div>
          <div className="mt-2 text-[13px] text-white/60 leading-relaxed">{c.desc}</div>
        </div>
      ))}
      <div className="md:col-span-3 mt-2 flex flex-wrap items-center gap-2 text-[12px] text-white/55">
        Try a sample:
        {samples.map((s) => (
          <button
            key={s}
            className="chip hover:bg-white/5 transition-colors"
            onClick={() => onPickSample(s)}
            data-testid={`sample-${s.replace(/[^a-z0-9]/gi, "-")}`}
          >
            {s.replace(/^https?:\/\//, "")}
          </button>
        ))}
      </div>
    </div>
  );
}

function PreviewMockup() {
  return (
    <div className="w-[78%] aspect-[16/10] rounded-xl border border-white/10 bg-[#0b1220]/70 backdrop-blur overflow-hidden shadow-2xl">
      <div className="h-7 bg-white/5 border-b border-white/10 flex items-center gap-1.5 px-3">
        <span className="size-2 rounded-full bg-white/20" />
        <span className="size-2 rounded-full bg-white/20" />
        <span className="size-2 rounded-full bg-white/20" />
        <div className="ml-3 flex-1 h-3 rounded bg-white/[0.06]" />
      </div>
      <div className="p-6 grid grid-cols-5 gap-4">
        <div className="col-span-3">
          <div className="h-2 w-24 rounded bg-white/[0.08]" />
          <div className="mt-5 h-6 w-[90%] rounded bg-white/[0.08]" />
          <div className="mt-3 h-6 w-[75%] rounded bg-white/[0.06]" />
          <div className="mt-6 h-8 w-32 rounded-lg bg-[var(--teal)]/70" />
        </div>
        <div className="col-span-2 aspect-video rounded-lg bg-gradient-to-br from-[var(--teal)]/30 via-white/10 to-[var(--ember)]/25 border border-white/10" />
      </div>
      <div className="px-6 pb-6 grid grid-cols-3 gap-3">
        {[0, 1, 2].map((i) => (
          <div key={i} className="h-16 rounded-lg border border-white/10 bg-white/[0.03]" />
        ))}
      </div>
    </div>
  );
}
