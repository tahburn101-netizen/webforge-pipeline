import { useEffect, useRef, useState } from "react";
import { eventsUrl, getJob } from "@/lib/api";

/**
 * Subscribe to a job's SSE stream.
 * Returns { job, logs, done } reactive state.
 */
export function useJobStream(jobId) {
  const [job, setJob] = useState(null);
  const [logs, setLogs] = useState([]);
  const [done, setDone] = useState(false);
  const esRef = useRef(null);

  useEffect(() => {
    if (!jobId) return;
    setJob(null);
    setLogs([]);
    setDone(false);

    // initial snapshot
    getJob(jobId).then(setJob).catch(() => {});

    const es = new EventSource(eventsUrl(jobId));
    esRef.current = es;
    es.addEventListener("job", (e) => {
      try {
        const data = JSON.parse(e.data);
        setJob(data);
      } catch {}
    });
    es.addEventListener("log", (e) => {
      try {
        const data = JSON.parse(e.data);
        setLogs((prev) => {
          // dedupe if historical replay overlaps
          const last = prev[prev.length - 1];
          if (last && last.ts === data.ts && last.message === data.message) return prev;
          return [...prev, data];
        });
      } catch {}
    });
    es.addEventListener("done", () => {
      setDone(true);
      es.close();
    });
    es.onerror = () => {
      // Let browser retry automatically; if job completed the server closes the stream.
    };
    return () => {
      es.close();
      esRef.current = null;
    };
  }, [jobId]);

  return { job, logs, done };
}
