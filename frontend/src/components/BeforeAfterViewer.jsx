import { useState } from "react";
import { artifactUrl } from "@/lib/api";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertTriangle, UserX, Eye, EyeOff } from "lucide-react";

export function BeforeAfterViewer({ job }) {
  const [device, setDevice] = useState("desktop");
  const [showOverlays, setShowOverlays] = useState(true);
  const originalKey = device === "desktop" ? "original_desktop" : "original_mobile";
  const genKey = device === "desktop" ? "generated_desktop" : "generated_mobile";
  const oname = job?.screenshots?.[originalKey];
  const gname = job?.screenshots?.[genKey];
  const oUrl = oname ? artifactUrl(job.id, oname) : null;
  const gUrl = gname ? artifactUrl(job.id, gname) : null;

  const qa = device === "desktop" ? job?.qa_generated : job?.qa_mobile;
  const overlaps = Array.isArray(qa?.overlap_regions) ? qa.overlap_regions : [];
  const humans = Array.isArray(qa?.human_detections) ? qa.human_detections : [];
  const hasDetections = overlaps.length + humans.length > 0;

  return (
    <div className="panel p-5" data-testid="before-after">
      <div className="flex items-center justify-between mb-4 gap-3 flex-wrap">
        <div>
          <div className="text-[11px] uppercase tracking-[0.18em] text-white/45">Preview</div>
          <div className="mt-1 text-lg font-semibold tracking-tight">Before &rarr; After</div>
        </div>
        <div className="flex items-center gap-2">
          {hasDetections && (
            <button
              className="btn-ghost h-8 text-[11px]"
              onClick={() => setShowOverlays((v) => !v)}
              data-testid="toggle-overlays"
            >
              {showOverlays ? <EyeOff size={11} /> : <Eye size={11} />}
              {showOverlays ? "Hide" : "Show"} QA overlays
            </button>
          )}
          <Tabs value={device} onValueChange={setDevice} data-testid="before-after-tabs">
            <TabsList className="bg-white/5 border border-white/10 h-8">
              <TabsTrigger value="desktop" className="text-xs data-[state=active]:bg-white/10">
                Desktop
              </TabsTrigger>
              <TabsTrigger value="mobile" className="text-xs data-[state=active]:bg-white/10">
                Mobile
              </TabsTrigger>
            </TabsList>
            <TabsContent value={device} />
          </Tabs>
        </div>
      </div>
      <div
        className={
          device === "desktop"
            ? "grid grid-cols-1 md:grid-cols-2 gap-3"
            : "grid grid-cols-2 gap-6 justify-items-center"
        }
      >
        <Frame
          label="Before"
          url={oUrl}
          device={device}
          testId="before-image"
          accent="rgba(255, 90, 122, 0.6)"
        />
        <Frame
          label="After"
          url={gUrl}
          device={device}
          testId="after-image"
          accent="var(--teal)"
          overlays={showOverlays ? { overlaps, humans } : null}
        />
      </div>
    </div>
  );
}

function Frame({ label, url, device, testId, accent, overlays }) {
  if (device === "mobile") {
    return (
      <div className="flex flex-col items-center gap-3">
        <div className="phone-frame w-[220px] aspect-[9/19] overflow-hidden relative">
          {url ? (
            <img
              src={url}
              alt={label}
              data-testid={testId}
              className="w-full h-full object-cover"
              loading="lazy"
            />
          ) : (
            <Skeleton className="w-full h-full" />
          )}
          {overlays && <DetectionOverlay overlays={overlays} />}
        </div>
        <div className="chip" style={{ color: accent }}>
          <span className="size-1.5 rounded-full" style={{ background: accent }} />
          {label}
        </div>
      </div>
    );
  }
  return (
    <div className="relative rounded-xl overflow-hidden border border-white/10 bg-black/30 aspect-[16/10]">
      {url ? (
        <img
          src={url}
          alt={label}
          data-testid={testId}
          className="w-full h-full object-cover"
          loading="lazy"
        />
      ) : (
        <Skeleton className="w-full h-full" />
      )}
      {overlays && <DetectionOverlay overlays={overlays} />}
      <div className="absolute top-3 left-3 chip" style={{ color: accent }}>
        <span className="size-1.5 rounded-full" style={{ background: accent }} />
        {label}
      </div>
    </div>
  );
}

/**
 * Draws normalized bounding boxes (x,y,w,h as fractions 0-1) over the image.
 * Red for overlap regions, amber for human detections.
 */
function DetectionOverlay({ overlays }) {
  const overlaps = overlays?.overlaps || [];
  const humans = overlays?.humans || [];
  if (overlaps.length + humans.length === 0) return null;
  return (
    <div className="absolute inset-0 pointer-events-none" data-testid="detection-overlay">
      {overlaps.map((b, i) => (
        <Box key={`o-${i}`} b={b} color="#FF5A7A" icon={<AlertTriangle size={10} />} />
      ))}
      {humans.map((b, i) => (
        <Box key={`h-${i}`} b={b} color="#FFCC66" icon={<UserX size={10} />} />
      ))}
    </div>
  );
}

function Box({ b, color, icon }) {
  const x = clamp01(Number(b.x) || 0) * 100;
  const y = clamp01(Number(b.y) || 0) * 100;
  const w = clamp01(Number(b.w) || 0) * 100;
  const h = clamp01(Number(b.h) || 0) * 100;
  if (w <= 0 || h <= 0) return null;
  return (
    <div
      className="absolute rounded-sm"
      style={{
        left: `${x}%`,
        top: `${y}%`,
        width: `${w}%`,
        height: `${h}%`,
        border: `1.5px solid ${color}`,
        background: `${color}1f`,
        boxShadow: `0 0 0 2px ${color}33`,
      }}
    >
      <div
        className="absolute -top-4 left-0 inline-flex items-center gap-1 px-1 rounded-sm text-[9px] font-mono"
        style={{ color, background: "rgba(0,0,0,0.7)" }}
      >
        {icon}
        {(b.label || "").slice(0, 40)}
      </div>
    </div>
  );
}

function clamp01(n) {
  if (!Number.isFinite(n)) return 0;
  return Math.max(0, Math.min(1, n));
}
