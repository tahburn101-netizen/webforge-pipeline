{
  "product": {
    "name": "Website Transformer Pipeline UI",
    "app_type": "saas_app",
    "audience": "Founders/creators who want an investor-ready redesign of an existing website in minutes",
    "north_star": "Make the pipeline feel as premium as the output: cinematic, confident, zero-jank real-time progress, and mobile-perfect."
  },
  "brand_attributes": [
    "cinematic",
    "high-end creative studio",
    "trustworthy (data-forward, not gimmicky)",
    "AI-native (real-time, artifact-driven)",
    "precise (QA gates, measurable scores)"
  ],
  "visual_personality": {
    "style_fusion": [
      "Linear.app-like information density + calm hierarchy",
      "Cursor/v0.dev-like AI-native pipeline feel (logs + artifacts)",
      "Cinematic studio lighting: deep charcoal + warm ember + cool teal accents",
      "Glass-lite surfaces (NOT heavy glass): subtle translucency only on large panels"
    ],
    "do_not": [
      "No purple-forward palettes",
      "No neon overload",
      "No gradients on reading surfaces",
      "No centered-page reading layout"
    ]
  },
  "palette_options": {
    "note": "Pick ONE option as the default theme. All options obey gradient restriction rules (gradients only as subtle section backdrops / decorative overlays).",
    "option_a_abyss_teal_ember": {
      "intent": "Cinematic dark with teal precision + ember highlights (investor-grade).",
      "tokens": {
        "bg": "#070A0E",
        "bg_2": "#0B1220",
        "panel": "rgba(255,255,255,0.04)",
        "panel_border": "rgba(255,255,255,0.08)",
        "text": "#EAF0FF",
        "muted_text": "rgba(234,240,255,0.68)",
        "faint_text": "rgba(234,240,255,0.48)",
        "primary": "#2DE3C6",
        "primary_2": "#0EA5A4",
        "accent": "#FFB86B",
        "danger": "#FF5A7A",
        "warning": "#FFCC66",
        "success": "#2DE3C6",
        "ring": "rgba(45,227,198,0.35)",
        "shadow": "0 18px 60px rgba(0,0,0,0.55)",
        "grid_line": "rgba(255,255,255,0.06)"
      },
      "allowed_background_gradient": {
        "usage": "Hero backdrop only (max 20% viewport height).",
        "css": "radial-gradient(900px 420px at 20% 10%, rgba(45,227,198,0.14), transparent 60%), radial-gradient(700px 360px at 80% 0%, rgba(255,184,107,0.10), transparent 55%)"
      }
    },
    "option_b_graphite_lime_copper": {
      "intent": "More editorial + industrial; lime for action, copper for warmth.",
      "tokens": {
        "bg": "#0A0B0D",
        "bg_2": "#111318",
        "panel": "rgba(255,255,255,0.035)",
        "panel_border": "rgba(255,255,255,0.075)",
        "text": "#F2F4F8",
        "muted_text": "rgba(242,244,248,0.68)",
        "primary": "#B6F23C",
        "accent": "#D08C60",
        "danger": "#FF4D6D",
        "ring": "rgba(182,242,60,0.28)",
        "grid_line": "rgba(255,255,255,0.055)"
      },
      "allowed_background_gradient": {
        "usage": "Hero backdrop only.",
        "css": "radial-gradient(900px 420px at 18% 8%, rgba(182,242,60,0.12), transparent 60%), radial-gradient(700px 360px at 82% 0%, rgba(208,140,96,0.10), transparent 55%)"
      }
    },
    "option_c_ink_ocean_peach": {
      "intent": "Softer, more approachable; still premium. Ocean blue for trust, peach for delight.",
      "tokens": {
        "bg": "#070B12",
        "bg_2": "#0B1424",
        "panel": "rgba(255,255,255,0.04)",
        "panel_border": "rgba(255,255,255,0.085)",
        "text": "#EAF2FF",
        "muted_text": "rgba(234,242,255,0.70)",
        "primary": "#4CC9F0",
        "accent": "#FFB199",
        "danger": "#FF5470",
        "ring": "rgba(76,201,240,0.30)",
        "grid_line": "rgba(255,255,255,0.06)"
      },
      "allowed_background_gradient": {
        "usage": "Hero backdrop only.",
        "css": "radial-gradient(900px 420px at 20% 10%, rgba(76,201,240,0.14), transparent 60%), radial-gradient(700px 360px at 80% 0%, rgba(255,177,153,0.10), transparent 55%)"
      }
    },
    "option_d_black_ice_silver": {
      "intent": "Ultra-minimal, almost monochrome; relies on motion + typography.",
      "tokens": {
        "bg": "#050607",
        "bg_2": "#0B0D10",
        "panel": "rgba(255,255,255,0.03)",
        "panel_border": "rgba(255,255,255,0.07)",
        "text": "#F5F7FA",
        "muted_text": "rgba(245,247,250,0.66)",
        "primary": "#9AE6FF",
        "accent": "#D7DCE3",
        "danger": "#FF4D6D",
        "ring": "rgba(154,230,255,0.26)",
        "grid_line": "rgba(255,255,255,0.05)"
      },
      "allowed_background_gradient": {
        "usage": "Hero backdrop only.",
        "css": "radial-gradient(900px 420px at 20% 10%, rgba(154,230,255,0.10), transparent 60%), radial-gradient(700px 360px at 80% 0%, rgba(215,220,227,0.08), transparent 55%)"
      }
    }
  },
  "design_tokens_css": {
    "instructions": "Main agent should replace current shadcn tokens in /app/frontend/src/index.css with ONE palette option (recommend option_a). Keep HSL tokens for shadcn compatibility; map hex -> HSL during implementation.",
    "additional_custom_properties": {
      "--noise-opacity": "0.06",
      "--panel-blur": "10px",
      "--radius-sm": "10px",
      "--radius-md": "14px",
      "--radius-lg": "18px",
      "--shadow-elev-1": "0 10px 30px rgba(0,0,0,0.35)",
      "--shadow-elev-2": "0 18px 60px rgba(0,0,0,0.55)",
      "--stroke-subtle": "rgba(255,255,255,0.08)",
      "--stroke-faint": "rgba(255,255,255,0.06)",
      "--focus-ring": "0 0 0 4px var(--ring)"
    }
  },
  "typography": {
    "font_pairing": {
      "heading": {
        "google_font": "Space Grotesk",
        "fallback": "ui-sans-serif, system-ui",
        "usage": "H1/H2, step titles, score numbers"
      },
      "body": {
        "google_font": "IBM Plex Sans",
        "fallback": "ui-sans-serif, system-ui",
        "usage": "Body, labels, helper text"
      },
      "mono": {
        "google_font": "IBM Plex Mono",
        "fallback": "ui-monospace, SFMono-Regular",
        "usage": "Log stream, code-ish artifacts"
      }
    },
    "scale": {
      "h1": "text-4xl sm:text-5xl lg:text-6xl font-semibold tracking-tight",
      "h2": "text-base md:text-lg font-medium text-muted-foreground",
      "section_title": "text-lg font-semibold",
      "card_title": "text-sm font-semibold tracking-tight",
      "body": "text-sm md:text-base",
      "small": "text-xs text-muted-foreground",
      "mono": "font-mono text-xs leading-5"
    },
    "numbers": {
      "score": "tabular-nums tracking-tight",
      "timings": "tabular-nums"
    }
  },
  "layout": {
    "grid": {
      "max_width": "max-w-[1200px]",
      "page_padding": "px-4 sm:px-6 lg:px-8",
      "desktop_columns": "12",
      "primary_layout": "Left: Pipeline (stepper + logs) | Right: Artifacts (before/after + QA + deploy)",
      "desktop_split": "lg:grid lg:grid-cols-12 lg:gap-6",
      "left_col": "lg:col-span-5",
      "right_col": "lg:col-span-7"
    },
    "spacing": {
      "section_gap": "gap-6",
      "card_padding": "p-4 sm:p-5",
      "stack_gap": "space-y-3",
      "breathing_room_rule": "Prefer 2–3x more spacing than default shadcn examples; avoid cramped panels."
    },
    "sticky_rules": {
      "desktop": "Make the right artifacts column sticky (top-6) so previews/QA stay visible while logs stream.",
      "mobile": "Disable sticky; use Tabs to switch between Pipeline / Preview / QA / Deploy."
    }
  },
  "components": {
    "global_shell": {
      "description": "App frame with top nav + subtle grid/noise background.",
      "shadcn": ["navigation-menu", "button", "badge", "separator"],
      "structure": {
        "top_nav": {
          "left": "Brand mark + product name",
          "center": "Nav: Pipeline, Jobs",
          "right": "Theme toggle (optional), Docs link, Status badge",
          "data_testids": {
            "nav-pipeline-link": "nav-pipeline-link",
            "nav-jobs-link": "nav-jobs-link"
          }
        },
        "background": {
          "tailwind": "bg-[radial-gradient(1200px_600px_at_20%_0%,rgba(45,227,198,0.10),transparent_60%),radial-gradient(900px_500px_at_80%_0%,rgba(255,184,107,0.08),transparent_55%)]",
          "overlay": "Add a noise overlay pseudo-element on body or a fixed div: opacity var(--noise-opacity)."
        }
      }
    },
    "url_input_hero": {
      "goal": "Minimal writing + immediate action. Feels like a command console for design transformation.",
      "shadcn": ["input", "button", "badge", "tooltip"],
      "layout": "Top of / page: compact hero with video background strip (not full screen) + URL command bar.",
      "spec": {
        "headline": "Transform any website into an investor-ready experience.",
        "subhead": "One URL in. QA-gated output. Public Vercel link out.",
        "command_bar": {
          "container_classes": "rounded-[var(--radius-lg)] border border-white/10 bg-white/[0.04] backdrop-blur-[var(--panel-blur)] shadow-[var(--shadow-elev-1)]",
          "input_classes": "h-12 bg-transparent border-0 focus-visible:ring-0 text-base placeholder:text-white/40",
          "button_variant": "primary",
          "button_classes": "h-12 px-5 rounded-xl",
          "left_icon": "lucide-react Link",
          "right_hint": "Press Enter",
          "data_testids": {
            "website-url-input": "website-url-input",
            "transform-submit-button": "transform-submit-button"
          }
        },
        "validation": {
          "error_text": "Show inline error under command bar using text-xs + destructive color.",
          "data_testid": "website-url-error"
        }
      },
      "micro_interactions": {
        "focus": "Command bar border brightens + subtle ring",
        "submit": "Button press scale 0.98; show spinner + 'Starting job…' toast",
        "idle": "Caret blink + faint animated scanline across bar (CSS keyframes, 6s)"
      }
    },
    "pipeline_stepper": {
      "goal": "6-stage pipeline with real-time status; readable at a glance.",
      "shadcn": ["progress", "badge", "collapsible", "separator"],
      "stages": ["Scrape", "Analyze", "Reference Match", "Generate Next.js", "QA Gates", "Deploy"],
      "spec": {
        "step_item": {
          "layout": "Left rail with dot + connector; right content with title + status badge + duration.",
          "states": {
            "pending": "dot: border-white/20 bg-transparent",
            "running": "dot: bg-primary shadow-[0_0_0_4px_rgba(45,227,198,0.12)] + subtle pulse",
            "done": "dot: bg-primary-foreground? (or primary) + check icon",
            "error": "dot: bg-destructive"
          },
          "data_testids": {
            "step": "pipeline-step-{slug}",
            "status": "pipeline-step-{slug}-status"
          }
        },
        "overall_progress": {
          "component": "shadcn Progress",
          "classes": "h-2 bg-white/10",
          "indicator": "bg-primary/80",
          "data_testid": "pipeline-overall-progress"
        }
      },
      "motion": {
        "running": "Framer Motion: animate dot scale [1,1.08,1] duration 1.6 repeat",
        "done": "Checkmark pops in (opacity+scale) 160ms",
        "error": "Shake step row 220ms (x: [0,-6,6,-4,4,0])"
      }
    },
    "log_stream": {
      "goal": "High-signal live logs without jank during SSE updates.",
      "shadcn": ["scroll-area", "tabs", "badge", "button"],
      "spec": {
        "container": "rounded-[var(--radius-md)] border border-white/10 bg-black/20 backdrop-blur-[var(--panel-blur)]",
        "header": "Tabs: All / Warnings / Errors + 'Auto-scroll' toggle",
        "body": "ScrollArea height: 320px (mobile 240px).",
        "row": {
          "font": "font-mono text-xs",
          "layout": "timestamp | stage badge | message",
          "colors": {
            "info": "text-white/70",
            "warn": "text-warning",
            "error": "text-destructive"
          },
          "data_testids": {
            "log-stream": "log-stream",
            "log-row": "log-row-{index}"
          }
        }
      },
      "performance_rules": [
        "Virtualize logs if > 300 rows (react-virtual or tanstack virtual).",
        "Batch SSE updates (requestAnimationFrame) to avoid reflow storms.",
        "Avoid heavy shadows inside scrolling container."
      ],
      "empty_loading_error": {
        "empty": "Show Skeleton rows + 'Waiting for events…'",
        "error": "Inline Alert with retry button (data-testid=log-stream-retry-button)"
      }
    },
    "qa_scorecards": {
      "goal": "Make QA feel like a gate with authority: numeric scores + short actionable notes.",
      "shadcn": ["card", "badge", "progress", "tooltip"],
      "cards": [
        "Anti-slop",
        "Palette quality",
        "Mobile perfection",
        "Overall"
      ],
      "spec": {
        "layout": "2x2 grid on desktop; 1 column on mobile.",
        "score": "Large number (text-3xl) + /100; color-coded ring.",
        "thresholds": {
          "pass": ">= 85",
          "warn": "70-84",
          "fail": "< 70"
        },
        "data_testids": {
          "qa-card": "qa-scorecard-{slug}",
          "qa-score": "qa-scorecard-{slug}-score",
          "qa-notes": "qa-scorecard-{slug}-notes"
        }
      },
      "micro_interactions": {
        "hover": "Card border brightens; show tooltip explaining rubric",
        "pass": "Subtle confetti is NOT allowed; instead do a calm glow sweep across the card (CSS gradient mask, 900ms)."
      }
    },
    "before_after_viewer": {
      "goal": "Investor-friendly proof: before/after desktop + mobile.",
      "shadcn": ["tabs", "card", "aspect-ratio", "skeleton", "slider"],
      "modes": ["Side-by-side", "Wipe"],
      "spec": {
        "tabs": "Desktop | Mobile",
        "desktop": "Two AspectRatio frames with labels 'Before' and 'After'",
        "mobile": "Phone frame mock (CSS) with screenshot inside",
        "wipe": "Use a comparison slider (can be custom using shadcn Slider + clipPath).",
        "data_testids": {
          "before-after-tabs": "before-after-tabs",
          "before-image": "before-image",
          "after-image": "after-image",
          "comparison-slider": "comparison-slider"
        }
      },
      "empty_loading_error": {
        "loading": "Skeleton blocks with shimmering (only on skeleton elements)",
        "empty": "Show 'Run a job to generate previews' + CTA to start",
        "error": "Alert with 'Re-capture screenshots' button"
      }
    },
    "video_upload_dropzone": {
      "goal": "Upload hero video for generated site; premium drag-drop with clear constraints.",
      "shadcn": ["card", "button", "progress", "tooltip"],
      "library": {
        "recommended": "react-dropzone",
        "install": "npm i react-dropzone",
        "note": "Use .js components (not .tsx)."
      },
      "spec": {
        "dropzone": {
          "classes": "rounded-[var(--radius-lg)] border border-dashed border-white/15 bg-white/[0.03] hover:bg-white/[0.05]",
          "states": {
            "idle": "Show icon + 'Drop MP4/WEBM'",
            "drag": "Border becomes primary/60 + background primary/10",
            "uploading": "Show Progress bar + cancel button",
            "done": "Show video preview thumbnail + replace button"
          },
          "data_testids": {
            "video-dropzone": "video-dropzone",
            "video-file-input": "video-file-input",
            "video-upload-cancel": "video-upload-cancel"
          }
        }
      }
    },
    "deploy_panel": {
      "goal": "Deploy is locked until QA passes; then one-click deploy + share.",
      "shadcn": ["card", "button", "badge", "tooltip", "separator"],
      "spec": {
        "locked_state": "Show badge 'QA required' + disabled deploy button + list failing checks.",
        "unlocked_state": "Primary deploy button + environment selector (optional) + estimated time.",
        "after_deploy": "Show public URL in read-only input + Copy button + QR code.",
        "data_testids": {
          "deploy-button": "deploy-button",
          "deploy-status": "deploy-status",
          "public-url-input": "public-url-input",
          "copy-public-url-button": "copy-public-url-button",
          "qr-code": "qr-code"
        }
      },
      "libraries": {
        "qr": {
          "recommended": "qrcode.react",
          "install": "npm i qrcode.react"
        }
      }
    },
    "jobs_list": {
      "route": "/jobs",
      "goal": "History of transformations with thumbnails + scores.",
      "shadcn": ["table", "card", "badge", "pagination", "input"],
      "spec": {
        "filters": "Search by domain + status chips",
        "rows": "Thumbnail | Domain | Date | Overall score | Status | Open",
        "data_testids": {
          "jobs-search-input": "jobs-search-input",
          "jobs-row": "jobs-row-{id}",
          "jobs-open-button": "jobs-open-button-{id}"
        }
      }
    },
    "job_detail": {
      "route": "/jobs/:id",
      "goal": "All artifacts: logs, screenshots, QA notes, deploy URL.",
      "shadcn": ["tabs", "card", "scroll-area", "badge", "separator"],
      "spec": {
        "tabs": ["Overview", "Artifacts", "Logs", "QA"],
        "data_testids": {
          "job-detail-tabs": "job-detail-tabs",
          "job-deploy-url": "job-deploy-url"
        }
      }
    }
  },
  "motion_principles": {
    "library": "framer-motion",
    "rules": [
      "Prefer opacity + translateY (6–10px) for entrances.",
      "Avoid animating box-shadow on every frame; use opacity/transform.",
      "SSE updates must not trigger layout thrash: animate only newly added rows.",
      "Respect prefers-reduced-motion: disable pulses, parallax, and explode effect."
    ],
    "presets": {
      "panel_enter": {"initial": "opacity-0 translate-y-2", "animate": "opacity-100 translate-y-0", "duration_ms": 220},
      "button_press": {"scale": 0.98, "duration_ms": 80},
      "subtle_hover": {"translateY": -1, "duration_ms": 140}
    }
  },
  "signature_interaction_exploding_hero": {
    "goal": "A premium 'explode on scroll' preview that demonstrates transformation energy without being gimmicky.",
    "implementation": {
      "library": "framer-motion (useScroll + useTransform)",
      "concept": "A compact hero video strip at top. As user scrolls 0→240px, the strip 'explodes' into separated layers: URL bar floats up slightly, background video scales down, and two preview cards slide outward (Before left, After right). Scrolling back reverses perfectly.",
      "constraints": [
        "Keep effect within first ~320px of page (avoid long parallax).",
        "No gradient text; keep copy minimal.",
        "On mobile: replace explode with a simple collapse into Tabs (Pipeline/Preview)."
      ],
      "data_testids": {
        "explode-hero": "explode-hero",
        "hero-video": "hero-video"
      }
    }
  },
  "accessibility": {
    "requirements": [
      "WCAG AA contrast for text on dark surfaces.",
      "Visible focus ring using --ring token.",
      "Keyboard navigation: stepper items, tabs, copy buttons.",
      "ARIA live region for pipeline status updates (polite).",
      "prefers-reduced-motion support."
    ],
    "testing_hooks": "All interactive + key informational elements must include data-testid in kebab-case."
  },
  "image_urls": {
    "decorative_backgrounds": [
      {
        "url": "https://images.unsplash.com/photo-1708305729900-906f34a7d49d?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA2ODl8MHwxfHNlYXJjaHwxfHxjaW5lbWF0aWMlMjBkYXJrJTIwYWJzdHJhY3QlMjBncmFkaWVudCUyMHRleHR1cmV8ZW58MHx8fHRlYWx8MTc3NzY2NjA2Nnww&ixlib=rb-4.1.0&q=85",
        "category": "background",
        "description": "Teal cinematic blur texture for subtle backdrop overlay (use at 4–6% opacity, large screens only)."
      },
      {
        "url": "https://images.unsplash.com/photo-1640030655997-7062bf40b23b?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1Mjh8MHwxfHNlYXJjaHwxfHxkYXJrJTIwY2luZW1hdGljJTIwd2FybSUyMG9yYW5nZSUyMGdsb3clMjBhYnN0cmFjdCUyMHRleHR1cmV8ZW58MHx8fG9yYW5nZXwxNzc3NjY2MDY5fDA&ixlib=rb-4.1.0&q=85",
        "category": "background",
        "description": "Warm ember blur texture for corner glow behind Deploy panel (use at 3–5% opacity)."
      }
    ],
    "hero_video": [
      {
        "url": "(user-uploaded)",
        "category": "video",
        "description": "Hero video for generated websites; in the tool UI show a muted looping placeholder until user uploads."
      }
    ]
  },
  "component_path": {
    "shadcn_ui": "/app/frontend/src/components/ui",
    "use_components": [
      "button.jsx",
      "input.jsx",
      "card.jsx",
      "tabs.jsx",
      "scroll-area.jsx",
      "progress.jsx",
      "badge.jsx",
      "separator.jsx",
      "tooltip.jsx",
      "dialog.jsx",
      "drawer.jsx",
      "skeleton.jsx",
      "sonner.jsx"
    ],
    "notes": [
      "Prefer Drawer for mobile panels (logs/QA) and Dialog for desktop modals.",
      "Use sonner for toasts."
    ]
  },
  "instructions_to_main_agent": [
    "Remove default CRA App.css centering patterns; do not center the entire app container.",
    "Set dark theme as default by applying class 'dark' on html/body/root and updating shadcn tokens in index.css.",
    "Implement /, /jobs, /jobs/:id routes with a consistent shell.",
    "Build the pipeline wizard as a two-column layout on desktop and Tabs/Drawer layout on mobile.",
    "Implement SSE log streaming with batching; animate only new rows.",
    "Add the signature 'explode on scroll' hero interaction on desktop only; provide reduced-motion fallback.",
    "Ensure every interactive element and key info has data-testid (kebab-case).",
    "Use lucide-react icons only (no emoji icons).",
    "Avoid gradients except subtle hero backdrops (<=20% viewport)."
  ],
  "General UI UX Design Guidelines": [
    "- You must **not** apply universal transition. Eg: `transition: all`. This results in breaking transforms. Always add transitions for specific interactive elements like button, input excluding transforms",
    "- You must **not** center align the app container, ie do not add `.App { text-align: center; }` in the css file. This disrupts the human natural reading flow of text",
    "- NEVER: use AI assistant Emoji characters like`🤖🧠💭💡🔮🎯📚🎭🎬🎪🎉🎊🎁🎀🎂🍰🎈🎨🎰💰💵💳🏦💎🪙💸🤑📊📈📉💹🔢🏆🥇 etc for icons. Always use **FontAwesome cdn** or **lucid-react** library already installed in the package.json",
    "\n **GRADIENT RESTRICTION RULE**",
    "NEVER use dark/saturated gradient combos (e.g., purple/pink) on any UI element.  Prohibited gradients: blue-500 to purple 600, purple 500 to pink-500, green-500 to blue-500, red to pink etc",
    "NEVER use dark gradients for logo, testimonial, footer etc",
    "NEVER let gradients cover more than 20% of the viewport.",
    "NEVER apply gradients to text-heavy content or reading areas.",
    "NEVER use gradients on small UI elements (<100px width).",
    "NEVER stack multiple gradient layers in the same viewport.",
    "\n **ENFORCEMENT RULE:**",
    "    • Id gradient area exceeds 20% of viewport OR affects readability, **THEN** use solid colors",
    "\n **How and where to use:**",
    "   • Section backgrounds (not content backgrounds)",
    "   • Hero section header content. Eg: dark to light to dark color",
    "   • Decorative overlays and accent elements only",
    "   • Hero section with 2-3 mild color",
    "   • Gradients creation can be done for any angle say horizontal, vertical or diagonal",
    "\n- For AI chat, voice application, **do not use purple color. Use color like light green, ocean blue, peach orange etc**",
    "\n\n</Font Guidelines>\n\n- Every interaction needs micro-animations - hover states, transitions, parallax effects, and entrance animations. Static = dead.\n   \n- Use 2-3x more spacing than feels comfortable. Cramped designs look cheap.\n\n- Subtle grain textures, noise overlays, custom cursors, selection states, and loading animations: separates good from extraordinary.\n   \n- Before generating UI, infer the visual style from the problem statement (palette, contrast, mood, motion) and immediately instantiate it by setting global design tokens (primary, secondary/accent, background, foreground, ring, state colors), rather than relying on any library defaults. Don't make the background dark as a default step, always understand problem first and define colors accordingly\n    Eg: - if it implies playful/energetic, choose a colorful scheme\n           - if it implies monochrome/minimal, choose a black–white/neutral scheme\n\n**Component Reuse:**\n\t- Prioritize using pre-existing components from src/components/ui when applicable\n\t- Create new components that match the style and conventions of existing components when needed\n\t- Examine existing components to understand the project's component patterns before creating new ones\n\n**IMPORTANT**: Do not use HTML based component like dropdown, calendar, toast etc. You **MUST** always use `/app/frontend/src/components/ui/ ` only as a primary components as these are modern and stylish component\n\n**Best Practices:**\n\t- Use Shadcn/UI as the primary component library for consistency and accessibility\n\t- Import path: ./components/[component-name]\n\n**Export Conventions:**\n\t- Components MUST use named exports (export const ComponentName = ...)\n\t- Pages MUST use default exports (export default function PageName() {...})\n\n**Toasts:**\n  - Use `sonner` for toasts\"\n  - Sonner component are located in `/app/src/components/ui/sonner.tsx`\n\nUse 2–4 color gradients, subtle textures/noise overlays, or CSS-based noise to avoid flat visuals."
  ]
}
