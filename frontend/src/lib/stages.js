export const STAGES = [
  { key: "scrape", label: "Scrape", desc: "Capture HTML + desktop/mobile shots" },
  { key: "analyze", label: "Analyze Original", desc: "Vision QA of the current site" },
  { key: "discover", label: "Discover References", desc: "Match awwwards + godly to your niche" },
  { key: "reference", label: "Extract Tokens", desc: "skillui reverse-engineers the reference" },
  { key: "plan", label: "Plan Site", desc: "Pages, palette, components picked" },
  { key: "review", label: "Review (2 min)", desc: "Edit the plan or let it continue" },
  { key: "generate", label: "Generate Next.js", desc: "Multi-page build + images" },
  { key: "taste", label: "Taste Polish", desc: "taste-skill polish pass" },
  { key: "qa_desktop", label: "QA Desktop", desc: "$25k rubric: overlap, no humans, premium feel" },
  { key: "qa_mobile", label: "QA Mobile", desc: "Dedicated mobile gate" },
  { key: "deploy", label: "Deploy", desc: "Public Vercel URL" },
];

export function stageIndex(key) {
  return STAGES.findIndex((s) => s.key === key);
}
