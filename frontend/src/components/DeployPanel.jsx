import { useEffect, useState } from "react";
import { QRCodeSVG } from "qrcode.react";
import { ExternalLink, Copy, Check, ShieldCheck, Rocket, Loader2 } from "lucide-react";
import { toast } from "sonner";

export function DeployPanel({ job }) {
  const [copied, setCopied] = useState(false);
  const [reveal, setReveal] = useState(false);
  const url = job?.deploy_url;
  const qaOk = (job?.qa_generated?.overall || 0) >= 70;
  const deploying = job?.status === "running" && (job?.steps || []).some((s) => s.key === "deploy" && s.status !== "done");
  const deployed = job?.status === "deployed" && !!url;

  useEffect(() => {
    if (!deployed) return;
    const t = setTimeout(() => setReveal(true), 120);
    return () => clearTimeout(t);
  }, [deployed]);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      toast.success("Public URL copied");
      setTimeout(() => setCopied(false), 1800);
    } catch {
      toast.error("Copy failed");
    }
  };

  return (
    <div className="panel p-5 relative overflow-hidden scanline" data-testid="deploy-panel">
      <div className="flex items-center justify-between mb-4">
        <div>
          <div className="text-[11px] uppercase tracking-[0.18em] text-white/45">Deploy</div>
          <div className="mt-1 text-lg font-semibold tracking-tight">
            Public URL &middot; no login required
          </div>
        </div>
        <div className="chip" data-testid="deploy-qa-status">
          <ShieldCheck size={11} />
          QA {qaOk ? "passed" : "pending"}
        </div>
      </div>
      {!deployed ? (
        <div className="rounded-xl border border-white/10 bg-white/[0.02] p-5 flex items-center gap-3">
          {deploying ? (
            <>
              <Loader2 size={16} className="animate-spin text-[var(--teal)]" />
              <div className="text-sm text-white/80" data-testid="deploy-status-text">
                Deploying to Vercel &middot; building Next.js...
              </div>
            </>
          ) : (
            <>
              <Rocket size={16} className="text-white/60" />
              <div className="text-sm text-white/60" data-testid="deploy-status-text">
                Waiting for pipeline to reach deploy stage
              </div>
            </>
          )}
        </div>
      ) : (
        <div
          className={`grid gap-4 md:grid-cols-[1fr_160px] items-start transition-opacity duration-500 ${
            reveal ? "opacity-100" : "opacity-0"
          }`}
        >
          <div>
            <div className="rounded-xl border border-white/10 bg-black/30 px-3 py-2 flex items-center gap-2">
              <input
                readOnly
                value={url || ""}
                data-testid="public-url-input"
                className="input-line h-10 text-sm mono flex-1"
              />
              <button className="btn-ghost h-9" onClick={copy} data-testid="copy-public-url-button">
                {copied ? <Check size={14} /> : <Copy size={14} />}
                {copied ? "Copied" : "Copy"}
              </button>
              <a
                className="btn-primary h-9"
                href={url}
                target="_blank"
                rel="noreferrer"
                data-testid="open-public-url"
              >
                Open <ExternalLink size={14} />
              </a>
            </div>
            <div className="mt-3 text-[12px] text-white/55">
              Share this with investors &mdash; the deployment has Vercel SSO protection
              disabled so the link is publicly accessible.
            </div>
          </div>
          <div className="rounded-xl border border-white/10 bg-white/[0.02] p-3 grid place-items-center">
            <div className="bg-white rounded-md p-2">
              <QRCodeSVG value={url || " "} size={128} bgColor="#ffffff" fgColor="#06101a" data-testid="qr-code" />
            </div>
            <div className="mt-2 text-[10px] uppercase tracking-[0.18em] text-white/45">Scan</div>
          </div>
        </div>
      )}
    </div>
  );
}
