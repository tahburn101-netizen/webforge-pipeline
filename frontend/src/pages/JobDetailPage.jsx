import { useParams, Link } from "react-router-dom";
import { useJobStream } from "@/lib/useJobStream";
import { PipelineStepper } from "@/components/PipelineStepper";
import { LogStream } from "@/components/LogStream";
import { BeforeAfterViewer } from "@/components/BeforeAfterViewer";
import { QACards } from "@/components/QACards";
import { DeployPanel } from "@/components/DeployPanel";
import { ArrowLeft } from "lucide-react";

export default function JobDetailPage() {
  const { id } = useParams();
  const { job, logs } = useJobStream(id);

  return (
    <div className="max-w-[1200px] mx-auto px-5 sm:px-8 py-10" data-testid="job-detail">
      <Link to="/jobs" className="inline-flex items-center gap-1.5 text-white/60 hover:text-white text-sm mb-6">
        <ArrowLeft size={14} /> All jobs
      </Link>
      <div className="mb-6">
        <div className="text-[11px] uppercase tracking-[0.18em] text-white/45">Job</div>
        <h1 className="font-display text-3xl sm:text-4xl font-semibold tracking-tight mt-1 break-all">
          {(job?.input_url || "...").replace(/^https?:\/\//, "")}
        </h1>
        <div className="mt-2 flex flex-wrap items-center gap-2 text-[12px] text-white/55">
          <span className="mono">{id.slice(0, 12)}</span>
          {job?.niche && <span className="chip">{job.niche}</span>}
          {job?.reference_url && (
            <span className="chip">
              ref:{" "}
              <span className="text-white/80 ml-1 mono">
                {job.reference_url.replace(/^https?:\/\//, "")}
              </span>
            </span>
          )}
          <span className="chip">status: {job?.status || "..."}</span>
        </div>
      </div>
      <div className="grid lg:grid-cols-12 gap-5">
        <div className="lg:col-span-5 space-y-5">
          <PipelineStepper steps={job?.steps || []} />
          <LogStream logs={logs} />
        </div>
        <div className="lg:col-span-7 space-y-5">
          <BeforeAfterViewer job={job} />
          <div className="grid md:grid-cols-2 gap-5">
            <QACards title="Original" scores={job?.qa_original} />
            <QACards title="Generated" scores={job?.qa_generated} />
          </div>
          <DeployPanel job={job} />
        </div>
      </div>
    </div>
  );
}
