import { useCallback, useMemo, useRef, useState } from "react";
import { useDropzone } from "react-dropzone";
import { toast } from "sonner";
import { UploadCloud, Film, X } from "lucide-react";
import { uploadVideo, API } from "@/lib/api";

export function VideoUpload({ jobId, currentAssetId, onUploaded }) {
  const [progress, setProgress] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [previewUrl, setPreviewUrl] = useState(
    currentAssetId ? `${API}/uploads/${currentAssetId}` : null
  );
  const cancelRef = useRef(null);

  const onDrop = useCallback(
    async (accepted) => {
      const file = accepted?.[0];
      if (!file) return;
      if (!jobId) {
        toast.error("Start a job first, then upload a video.");
        return;
      }
      const ok = ["video/mp4", "video/webm", "video/quicktime"].includes(file.type);
      if (!ok) {
        toast.error("Only MP4 / WEBM / MOV supported.");
        return;
      }
      setUploading(true);
      setProgress(0);
      try {
        const data = await uploadVideo(jobId, file, (p) => setProgress(p));
        setPreviewUrl(`${API}/uploads/${data.asset_id}`);
        toast.success("Hero video uploaded");
        onUploaded?.(data);
      } catch (e) {
        toast.error(e?.response?.data?.detail || "Upload failed");
      } finally {
        setUploading(false);
        setProgress(0);
      }
    },
    [jobId, onUploaded]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: false,
    accept: { "video/mp4": [".mp4"], "video/webm": [".webm"], "video/quicktime": [".mov"] },
    disabled: uploading,
  });

  const rootStyle = useMemo(
    () =>
      `rounded-xl border border-dashed px-5 py-6 transition-colors cursor-pointer ${
        isDragActive
          ? "border-[var(--teal)] bg-[var(--teal)]/10"
          : "border-white/15 bg-white/[0.02] hover:bg-white/[0.04]"
      } ${uploading ? "opacity-60 cursor-progress" : ""}`,
    [isDragActive, uploading]
  );

  return (
    <div className="panel p-5" data-testid="video-upload-panel">
      <div className="flex items-center justify-between mb-3">
        <div>
          <div className="text-[11px] uppercase tracking-[0.18em] text-white/45">Hero video</div>
          <div className="mt-1 text-lg font-semibold tracking-tight">Upload 4K MP4 / WEBM</div>
        </div>
        {previewUrl && (
          <button
            className="btn-ghost h-8 text-xs"
            onClick={() => setPreviewUrl(null)}
            data-testid="video-upload-clear"
          >
            <X size={12} /> Replace
          </button>
        )}
      </div>
      {previewUrl ? (
        <div className="rounded-xl overflow-hidden border border-white/10 aspect-video bg-black">
          <video
            src={previewUrl}
            autoPlay
            muted
            loop
            playsInline
            className="w-full h-full object-cover"
            data-testid="video-preview"
          />
        </div>
      ) : (
        <div {...getRootProps({ className: rootStyle })} data-testid="video-dropzone">
          <input {...getInputProps()} data-testid="video-file-input" ref={cancelRef} />
          <div className="flex items-center gap-4">
            <div className="size-12 rounded-xl border border-white/10 bg-white/5 grid place-items-center">
              <UploadCloud size={20} className="text-[var(--teal)]" />
            </div>
            <div>
              <div className="text-sm font-medium">
                {isDragActive ? "Drop to upload" : "Drag & drop a video, or click to browse"}
              </div>
              <div className="text-xs text-white/50 mt-0.5">
                MP4 or WEBM. 4K recommended. Will play as the looping hero on your generated site.
              </div>
            </div>
          </div>
          {uploading && (
            <div className="mt-3 h-1 rounded-full bg-white/5 overflow-hidden">
              <div
                className="h-full bg-[var(--teal)] transition-[width] duration-150"
                style={{ width: `${progress}%` }}
              />
            </div>
          )}
        </div>
      )}
      <div className="mt-3 text-[11px] text-white/45 flex items-center gap-1.5">
        <Film size={12} /> Optional. If omitted, we render a cinematic animated backdrop.
      </div>
    </div>
  );
}
