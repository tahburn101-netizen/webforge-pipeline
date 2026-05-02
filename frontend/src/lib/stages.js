export const STAGES = [
  { key: "scrape", label: "Scrape", desc: "Capture HTML + desktop/mobile shots" },
  { key: "analyze", label: "Analyze", desc: "Vision QA of the current site" },
  { key: "reference", label: "Reference Match", desc: "Extract design system via skillui" },
  { key: "generate", label: "Generate Next.js", desc: "Multi-page site with exploding hero" },
  { key: "qa", label: "QA Gates", desc: "Anti-slop, palette, mobile perfection" },
  { key: "deploy", label: "Deploy", desc: "Ship a public Vercel URL" },
];

export function stageIndex(key) {
  return STAGES.findIndex((s) => s.key === key);
}
