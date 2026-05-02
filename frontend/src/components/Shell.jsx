import { Link, NavLink } from "react-router-dom";
import { Orbit, Layers } from "lucide-react";

export function Shell({ children }) {
  return (
    <div className="relative min-h-screen shell-bg noise">
      <header className="sticky top-0 z-40 backdrop-blur-md bg-[color:var(--bg-0)]/70 border-b border-white/5">
        <div className="max-w-[1200px] mx-auto h-14 px-5 sm:px-8 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 group" data-testid="brand-link">
            <div className="relative size-7 rounded-lg bg-gradient-to-br from-[var(--teal)] to-[var(--teal-2)] grid place-items-center glow-teal">
              <Orbit size={14} className="text-[var(--bg-0)]" />
            </div>
            <div className="leading-none">
              <div className="text-[15px] font-semibold tracking-tight">WebForge</div>
              <div className="text-[10px] uppercase tracking-[0.18em] text-white/45">
                Pipeline
              </div>
            </div>
          </Link>
          <nav className="flex items-center gap-1 text-sm">
            <NavLink
              to="/"
              end
              data-testid="nav-pipeline-link"
              className={({ isActive }) =>
                `px-3 py-1.5 rounded-md transition-colors ${
                  isActive
                    ? "text-white bg-white/[0.06]"
                    : "text-white/60 hover:text-white hover:bg-white/[0.04]"
                }`
              }
            >
              Pipeline
            </NavLink>
            <NavLink
              to="/jobs"
              data-testid="nav-jobs-link"
              className={({ isActive }) =>
                `px-3 py-1.5 rounded-md transition-colors ${
                  isActive
                    ? "text-white bg-white/[0.06]"
                    : "text-white/60 hover:text-white hover:bg-white/[0.04]"
                }`
              }
            >
              <span className="inline-flex items-center gap-1.5">
                <Layers size={13} /> Jobs
              </span>
            </NavLink>
          </nav>
          <div className="hidden sm:flex items-center gap-2">
            <span className="chip" data-testid="status-chip">
              <span className="size-1.5 rounded-full bg-[var(--teal)] animate-pulse" />
              Online
            </span>
          </div>
        </div>
      </header>
      <div className="relative z-10">{children}</div>
    </div>
  );
}
