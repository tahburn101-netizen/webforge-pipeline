import { useState } from "react";
import { artifactUrl } from "@/lib/api";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";

export function BeforeAfterViewer({ job }) {
  const [device, setDevice] = useState("desktop");
  const originalKey = device === "desktop" ? "original_desktop" : "original_mobile";
  const genKey = device === "desktop" ? "generated_desktop" : "generated_mobile";
  const oname = job?.screenshots?.[originalKey];
  const gname = job?.screenshots?.[genKey];
  const oUrl = oname ? artifactUrl(job.id, oname) : null;
  const gUrl = gname ? artifactUrl(job.id, gname) : null;

  return (
    <div className="panel p-5" data-testid="before-after">
      <div className="flex items-center justify-between mb-4">
        <div>
          <div className="text-[11px] uppercase tracking-[0.18em] text-white/45">Preview</div>
          <div className="mt-1 text-lg font-semibold tracking-tight">Before &rarr; After</div>
        </div>
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
        />
      </div>
    </div>
  );
}

function Frame({ label, url, device, testId, accent }) {
  if (device === "mobile") {
    return (
      <div className="flex flex-col items-center gap-3">
        <div className="phone-frame w-[220px] aspect-[9/19] overflow-hidden">
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
      <div className="absolute top-3 left-3 chip" style={{ color: accent }}>
        <span className="size-1.5 rounded-full" style={{ background: accent }} />
        {label}
      </div>
    </div>
  );
}
