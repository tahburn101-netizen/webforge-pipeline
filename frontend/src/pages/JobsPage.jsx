import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listJobs, deleteJob, artifactUrl } from "@/lib/api";
import { ArrowUpRight, Trash2, ExternalLink, Search } from "lucide-react";
import { toast } from "sonner";

export default function JobsPage() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const data = await listJobs();
      setJobs(data);
    } catch (e) {
      toast.error("Failed to load jobs");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const filtered = jobs.filter((j) => {
    if (!q) return true;
    const s = q.toLowerCase();
    return (
      (j.input_url || "").toLowerCase().includes(s) ||
      (j.niche || "").toLowerCase().includes(s) ||
      (j.deploy_url || "").toLowerCase().includes(s)
    );
  });

  return (
    <div className="max-w-[1200px] mx-auto px-5 sm:px-8 py-12">
      <div className="flex items-center justify-between mb-6">
        <div>
          <div className="text-[11px] uppercase tracking-[0.18em] text-white/45">Jobs</div>
          <h1 className="font-display text-3xl sm:text-4xl font-semibold tracking-tight">
            Transformation history
          </h1>
        </div>
        <div className="relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-white/40" />
          <input
            className="pl-8 pr-3 h-10 rounded-xl bg-white/[0.04] border border-white/10 text-sm outline-none focus:border-[var(--teal)]/40 w-72"
            placeholder="Search URL, niche…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            data-testid="jobs-search-input"
          />
        </div>
      </div>
      {loading ? (
        <div className="panel p-8 text-center text-white/50">Loading…</div>
      ) : filtered.length === 0 ? (
        <div className="panel p-10 text-center">
          <div className="text-white/60">No jobs yet.</div>
          <Link to="/" className="btn-primary mt-4 inline-flex">
            Start a transformation <ArrowUpRight size={14} />
          </Link>
        </div>
      ) : (
        <div className="grid gap-3">
          {filtered.map((j) => (
            <JobRow key={j.id} j={j} onDelete={load} />
          ))}
        </div>
      )}
    </div>
  );
}

function JobRow({ j, onDelete }) {
  const thumb = j.screenshots?.generated_desktop || j.screenshots?.original_desktop;
  const thumbUrl = thumb ? artifactUrl(j.id, thumb) : null;
  const overall = j.qa_generated?.overall || 0;
  const statusColor =
    j.status === "deployed"
      ? "text-[var(--teal)]"
      : j.status === "failed"
      ? "text-rose-400"
      : "text-white/70";
  return (
    <div
      className="panel p-3 flex items-center gap-4 hover:bg-white/[0.05] transition-colors"
      data-testid={`jobs-row-${j.id}`}
    >
      <Link to={`/jobs/${j.id}`} className="flex items-center gap-4 flex-1 min-w-0">
        <div className="w-28 aspect-video rounded-lg border border-white/10 bg-black/30 overflow-hidden shrink-0">
          {thumbUrl ? (
            <img src={thumbUrl} alt="" className="w-full h-full object-cover" loading="lazy" />
          ) : (
            <div className="w-full h-full bg-gradient-to-br from-white/5 to-white/[0.02]" />
          )}
        </div>
        <div className="min-w-0 flex-1">
          <div className="text-[13px] text-white/60 truncate">
            {(j.input_url || "").replace(/^https?:\/\//, "")}
          </div>
          <div className="text-sm font-medium tracking-tight mt-0.5 truncate">
            {j.niche || "Pending analysis"}
          </div>
          <div className="text-[11px] text-white/40 mt-1 mono">{j.id.slice(0, 8)}</div>
        </div>
        <div className="hidden sm:block text-right">
          <div className="text-2xl font-display font-semibold tabular-nums" style={{ color: overall >= 70 ? "var(--teal)" : overall > 0 ? "#FFCC66" : "rgba(255,255,255,0.4)" }}>
            {overall || "—"}
          </div>
          <div className="text-[10px] uppercase tracking-[0.16em] text-white/40">overall</div>
        </div>
        <div className={`chip ${statusColor}`}>
          <span className="size-1.5 rounded-full" style={{ background: "currentColor" }} />
          {j.status}
        </div>
      </Link>
      <div className="flex items-center gap-2 shrink-0">
        {j.deploy_url && (
          <a
            href={j.deploy_url}
            target="_blank"
            rel="noreferrer"
            className="btn-ghost h-9 text-xs"
            data-testid="jobs-open-deploy"
          >
            Live <ExternalLink size={12} />
          </a>
        )}
        <button
          className="btn-ghost h-9 text-xs text-white/50 hover:text-rose-300"
          onClick={async () => {
            if (!confirm("Delete this job?")) return;
            await deleteJob(j.id);
            toast.success("Deleted");
            onDelete?.();
          }}
          data-testid="jobs-delete"
        >
          <Trash2 size={12} />
        </button>
      </div>
    </div>
  );
}
