// Node-oriented editable pro deck builder.
// Run this after editing SLIDES, SOURCES, and layout functions.
// The init script installs a sibling node_modules/@oai/artifact-tool package link
// and package.json with type=module for shell-run eval builders. Run with the
// Node executable from Codex workspace dependencies or the platform-appropriate
// command emitted by the init script.
// Do not use pnpm exec from the repo root or any Node binary whose module
// lookup cannot resolve the builder's sibling node_modules/@oai/artifact-tool.

const fs = await import("node:fs/promises");
const path = await import("node:path");
const { Presentation, PresentationFile } = await import("@oai/artifact-tool");

const W = 1280;
const H = 720;

const DECK_ID = "foodsprint-ai-assisted-project";
const OUT_DIR = "C:\\Users\\spand\\OneDrive\\Documents\\New project\\outputs\\foodsprint-ai-assisted-project";
const REF_DIR = "C:\\Users\\spand\\OneDrive\\Documents\\New project\\tmp\\slides\\foodsprint-ai-assisted-project\\reference";
const ASSET_DIR = "C:\\Users\\spand\\OneDrive\\Documents\\New project\\tmp\\slides\\foodsprint-ai-assisted-project\\assets";
const SCRATCH_DIR = path.resolve(process.env.PPTX_SCRATCH_DIR || path.join("tmp", "slides", DECK_ID));
const PREVIEW_DIR = path.join(SCRATCH_DIR, "preview");
const VERIFICATION_DIR = path.join(SCRATCH_DIR, "verification");
const INSPECT_PATH = path.join(SCRATCH_DIR, "inspect.ndjson");
const MAX_RENDER_VERIFY_LOOPS = 3;

const INK = "#101214";
const GRAPHITE = "#30363A";
const MUTED = "#687076";
const PAPER = "#F7F4ED";
const PAPER_96 = "#F7F4EDF5";
const WHITE = "#FFFFFF";
const ACCENT = "#FC8019";
const ACCENT_DARK = "#A64F0C";
const GOLD = "#27C47D";
const CORAL = "#E86F5B";
const TRANSPARENT = "#00000000";
const NAVY = "#0F172A";
const NAVY_LINE = "#22304A";
const SOFT_ORANGE = "#FFF1E4";
const SOFT_GREEN = "#EAF9F1";

const TITLE_FACE = "Segoe UI";
const BODY_FACE = "Segoe UI";
const MONO_FACE = "Consolas";

const FALLBACK_PLATE_DATA_URL =
  "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII=";

const SOURCES = {
  repo: "Local FoodSprint repository: README.md, app/routes.py, app/services/image_utils.py, app/services/data_seed.py.",
  conversation: "Project prompts and AI-assisted change requests from the working session.",
};

const SLIDES = [
  {
    "layout": "cover",
    "kicker": "AI ASSISTED CODING PROJECT",
    "title": "FoodSprint",
    "subtitle": "A Flask web app for Telangana restaurant discovery, UPI checkout, diet recommendations, and admin or staff order operations.",
    "moment": "Prompt-driven development from idea to documentation and review",
    "highlights": [
      "Nearby discovery with OpenStreetMap and Overpass",
      "UPI QR checkout and order tracking",
      "AI-assisted README and code review workflow"
    ],
    "notes": "Introduce FoodSprint as a practical AI-assisted coding project with real user flows and maintainable structure.",
    "sources": [
      "repo",
      "conversation"
    ]
  },
  {
    "layout": "cards",
    "kicker": "PROJECT SCOPE",
    "title": "Problem statement and project goal",
    "subtitle": "FoodSprint combines restaurant discovery, ordering, payment, and operations management in one demo product.",
    "cards": [
      [
        "User need",
        "Users need one place to discover restaurants near them, browse menus, place orders, and track status without switching tools."
      ],
      [
        "Project scope",
        "The app focuses on Telangana restaurant discovery, UPI QR payment, order tracking, diet-aware suggestions, and role-based dashboards."
      ],
      [
        "Operations view",
        "Admin and staff flows strengthen the app by covering payment setup, staff access, and order fulfillment updates."
      ]
    ],
    "notes": "Explain the app as a realistic end-to-end product demo rather than only a static UI project.",
    "sources": [
      "repo"
    ]
  },
  {
    "layout": "metrics",
    "kicker": "FEATURE SNAPSHOT",
    "title": "Implemented feature summary",
    "subtitle": "The current codebase already supports a complete multi-role demo workflow.",
    "metrics": [
      [
        "11",
        "Seeded restaurants",
        "Across Hyderabad, Warangal, Karimnagar, Nizamabad, and Khammam"
      ],
      [
        "110",
        "Menu items",
        "Ten menu items per restaurant in the seeded catalog"
      ],
      [
        "3",
        "Primary roles",
        "Customer, admin, and staff flows are implemented"
      ]
    ],
    "notes": "Use this slide to show that the project has meaningful scope and concrete implementation depth.",
    "sources": [
      "repo"
    ]
  },
  {
    "layout": "cards",
    "kicker": "SYSTEM DESIGN",
    "title": "Architecture and technology stack",
    "subtitle": "FoodSprint uses a compact Flask architecture with clear service boundaries and practical integrations.",
    "cards": [
      [
        "Frontend",
        "Jinja templates, CSS, JavaScript, Leaflet maps, nearby filters, and mini-cart interactions create the user-facing experience."
      ],
      [
        "Backend",
        "Flask routes, SQLAlchemy models, recommendation services, payment helpers, and order status workflows handle business logic."
      ],
      [
        "Data and integrations",
        "SQLite or PostgreSQL stores the data layer, while OpenStreetMap, Overpass, and UPI QR generation support discovery and checkout."
      ]
    ],
    "notes": "Walk the audience from UI to backend logic to external integrations.",
    "sources": [
      "repo"
    ]
  },
  {
    "layout": "cards",
    "kicker": "AI WORKFLOW",
    "title": "How AI assisted the development process",
    "subtitle": "The project benefits from prompt-driven iteration, code inspection, targeted edits, and fast documentation updates.",
    "cards": [
      [
        "Prompt",
        "Changes start from natural-language instructions such as updating README content or investigating broken website images."
      ],
      [
        "Inspect and patch",
        "AI reviews routes, services, templates, and config files before applying focused improvements inside the repository."
      ],
      [
        "Verify and present",
        "The result is checked, summarized for GitHub or demos, and turned into supporting material such as this presentation."
      ]
    ],
    "notes": "Frame AI as an assistant for productivity and code understanding, not as a replacement for project ownership.",
    "sources": [
      "repo",
      "conversation"
    ]
  },
  {
    "layout": "code",
    "kicker": "PROMPT TO CODE",
    "title": "Example 1: README documentation update",
    "subtitle": "A simple prompt was translated into a repo-aware documentation change that matches the current feature set.",
    "promptText": "I want to update README in GitHub about current features",
    "imagePath": "C:\\Users\\spand\\OneDrive\\Documents\\New project\\tmp\\slides\\foodsprint-ai-assisted-project\\assets\\readme_prompt.png",
    "takeaways": [
      "AI inspected the existing README before changing it.",
      "Outdated text was replaced with the features actually present in the codebase.",
      "The final README became clearer for GitHub visitors and deployment reviewers."
    ],
    "notes": "Use this example to show documentation support through AI-assisted repo inspection and rewriting.",
    "sources": [
      "repo",
      "conversation"
    ]
  },
  {
    "layout": "code",
    "kicker": "PROMPT TO CODE",
    "title": "Example 2: image quality review",
    "subtitle": "A visual issue on the website was traced back to image URL mappings in the service layer.",
    "promptText": "Some pictures are not proper in the website",
    "imagePath": "C:\\Users\\spand\\OneDrive\\Documents\\New project\\tmp\\slides\\foodsprint-ai-assisted-project\\assets\\image_prompt.png",
    "takeaways": [
      "AI can quickly inspect where image sources are assigned in the codebase.",
      "Broken or weak external image links become easier to identify and replace.",
      "This improves website quality while keeping the fix targeted and maintainable."
    ],
    "notes": "Use this example to explain how AI-assisted debugging can narrow a UI problem to a specific service file.",
    "sources": [
      "repo",
      "conversation"
    ]
  },
  {
    "layout": "commands",
    "kicker": "NEXT STEPS",
    "title": "Commands you can run after this",
    "subtitle": "These commands help you run the app, save your changes, and push the project to GitHub.",
    "commandText": "# Run locally\\npip install -r requirements.txt\\npython run.py\\n# Save current work\\ngit add .\\ngit commit -m \"Update FoodSprint project files\"\\n# Push to GitHub\\ngit push\\n# Optional Docker run\\ndocker compose up --build",
    "cards": [
      [
        "Local run",
        "Use pip plus python run.py when you want to demo the app quickly from the project folder."
      ],
      [
        "GitHub push",
        "Commit your final changes first, then push the branch to update the repository."
      ],
      [
        "Deployment",
        "Deploy only when code or configuration changed. README or PPT-only updates do not require a full redeploy."
      ]
    ],
    "notes": "End the deck with practical next steps the reviewer or project owner can actually use.",
    "sources": [
      "repo",
      "conversation"
    ]
  }
];

const inspectRecords = [];

async function pathExists(filePath) {
  try {
    await fs.access(filePath);
    return true;
  } catch {
    return false;
  }
}

async function readImageBlob(imagePath) {
  const bytes = await fs.readFile(imagePath);
  if (!bytes.byteLength) {
    throw new Error(`Image file is empty: ${imagePath}`);
  }
  return bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
}

async function normalizeImageConfig(config) {
  if (!config.path) {
    return config;
  }
  const { path: imagePath, ...rest } = config;
  return {
    ...rest,
    blob: await readImageBlob(imagePath),
  };
}

async function ensureDirs() {
  await fs.mkdir(OUT_DIR, { recursive: true });
  const obsoleteFinalArtifacts = [
    "preview",
    "verification",
    "inspect.ndjson",
    ["presentation", "proto.json"].join("_"),
    ["quality", "report.json"].join("_"),
  ];
  for (const obsolete of obsoleteFinalArtifacts) {
    await fs.rm(path.join(OUT_DIR, obsolete), { recursive: true, force: true });
  }
  await fs.mkdir(SCRATCH_DIR, { recursive: true });
  await fs.mkdir(PREVIEW_DIR, { recursive: true });
  await fs.mkdir(VERIFICATION_DIR, { recursive: true });
}

function lineConfig(fill = TRANSPARENT, width = 0) {
  return { style: "solid", fill, width };
}

function recordShape(slideNo, shape, role, shapeType, x, y, w, h) {
  if (!slideNo) return;
  inspectRecords.push({
    kind: "shape",
    slide: slideNo,
    id: shape?.id || `slide-${slideNo}-${role}-${inspectRecords.length + 1}`,
    role,
    shapeType,
    bbox: [x, y, w, h],
  });
}

function addShape(slide, geometry, x, y, w, h, fill = TRANSPARENT, line = TRANSPARENT, lineWidth = 0, meta = {}) {
  const shape = slide.shapes.add({
    geometry,
    position: { left: x, top: y, width: w, height: h },
    fill,
    line: lineConfig(line, lineWidth),
  });
  recordShape(meta.slideNo, shape, meta.role || geometry, geometry, x, y, w, h);
  return shape;
}

function normalizeText(text) {
  if (Array.isArray(text)) {
    return text.map((item) => String(item ?? "")).join("\n");
  }
  return String(text ?? "");
}

function textLineCount(text) {
  const value = normalizeText(text);
  if (!value.trim()) {
    return 0;
  }
  return Math.max(1, value.split(/\n/).length);
}

function requiredTextHeight(text, fontSize, lineHeight = 1.18, minHeight = 8) {
  const lines = textLineCount(text);
  if (lines === 0) {
    return minHeight;
  }
  return Math.max(minHeight, lines * fontSize * lineHeight);
}

function assertTextFits(text, boxHeight, fontSize, role = "text") {
  const required = requiredTextHeight(text, fontSize);
  const tolerance = Math.max(2, fontSize * 0.08);
  if (normalizeText(text).trim() && boxHeight + tolerance < required) {
    throw new Error(
      `${role} text box is too short: height=${boxHeight.toFixed(1)}, required>=${required.toFixed(1)}, ` +
        `lines=${textLineCount(text)}, fontSize=${fontSize}, text=${JSON.stringify(normalizeText(text).slice(0, 90))}`,
    );
  }
}

function wrapText(text, widthChars) {
  const words = normalizeText(text).split(/\s+/).filter(Boolean);
  const lines = [];
  let current = "";
  for (const word of words) {
    const next = current ? `${current} ${word}` : word;
    if (next.length > widthChars && current) {
      lines.push(current);
      current = word;
    } else {
      current = next;
    }
  }
  if (current) {
    lines.push(current);
  }
  return lines.join("\n");
}

function recordText(slideNo, shape, role, text, x, y, w, h) {
  const value = normalizeText(text);
  inspectRecords.push({
    kind: "textbox",
    slide: slideNo,
    id: shape?.id || `slide-${slideNo}-${role}-${inspectRecords.length + 1}`,
    role,
    text: value,
    textPreview: value.replace(/\n/g, " | ").slice(0, 180),
    textChars: value.length,
    textLines: textLineCount(value),
    bbox: [x, y, w, h],
  });
}

function recordImage(slideNo, image, role, imagePath, x, y, w, h) {
  inspectRecords.push({
    kind: "image",
    slide: slideNo,
    id: image?.id || `slide-${slideNo}-${role}-${inspectRecords.length + 1}`,
    role,
    path: imagePath,
    bbox: [x, y, w, h],
  });
}

function applyTextStyle(box, text, size, color, bold, face, align, valign, autoFit, listStyle) {
  box.text = text;
  box.text.fontSize = size;
  box.text.color = color;
  box.text.bold = Boolean(bold);
  box.text.alignment = align;
  box.text.verticalAlignment = valign;
  box.text.typeface = face;
  box.text.insets = { left: 0, right: 0, top: 0, bottom: 0 };
  if (autoFit) {
    box.text.autoFit = autoFit;
  }
  if (listStyle) {
    box.text.style = "list";
  }
}

function addText(
  slide,
  slideNo,
  text,
  x,
  y,
  w,
  h,
  {
    size = 22,
    color = INK,
    bold = false,
    face = BODY_FACE,
    align = "left",
    valign = "top",
    fill = TRANSPARENT,
    line = TRANSPARENT,
    lineWidth = 0,
    autoFit = null,
    listStyle = false,
    checkFit = true,
    role = "text",
  } = {},
) {
  if (!checkFit && textLineCount(text) > 1) {
    throw new Error("checkFit=false is only allowed for single-line headers, footers, and captions.");
  }
  if (checkFit) {
    assertTextFits(text, h, size, role);
  }
  const box = addShape(slide, "rect", x, y, w, h, fill, line, lineWidth);
  applyTextStyle(box, text, size, color, bold, face, align, valign, autoFit, listStyle);
  recordText(slideNo, box, role, text, x, y, w, h);
  return box;
}

async function addImage(slide, slideNo, config, position, role, sourcePath = null) {
  const image = slide.images.add(await normalizeImageConfig(config));
  image.position = position;
  recordImage(slideNo, image, role, sourcePath || config.path || config.uri || "inline-data-url", position.left, position.top, position.width, position.height);
  return image;
}

async function addPlate(slide, slideNo, opacityPanel = false) {
  slide.background.fill = PAPER;
  const platePath = path.join(REF_DIR, `slide-${String(slideNo).padStart(2, "0")}.png`);
  if (await pathExists(platePath)) {
    await addImage(
      slide,
      slideNo,
      { path: platePath, fit: "cover", alt: `Text-free art-direction plate for slide ${slideNo}` },
      { left: 0, top: 0, width: W, height: H },
      "art plate",
      platePath,
    );
  } else {
    await addImage(
      slide,
      slideNo,
      { dataUrl: FALLBACK_PLATE_DATA_URL, fit: "cover", alt: `Fallback blank art plate for slide ${slideNo}` },
      { left: 0, top: 0, width: W, height: H },
      "fallback art plate",
      "fallback-data-url",
    );
  }
  if (opacityPanel) {
    addShape(slide, "rect", 0, 0, W, H, "#FFFFFFB8", TRANSPARENT, 0, { slideNo, role: "plate readability overlay" });
  }
}

function addHeader(slide, slideNo, kicker, idx, total) {
  addText(slide, slideNo, String(kicker || "").toUpperCase(), 64, 34, 430, 24, {
    size: 13,
    color: ACCENT_DARK,
    bold: true,
    face: MONO_FACE,
    checkFit: false,
    role: "header",
  });
  addText(slide, slideNo, `${String(idx).padStart(2, "0")} / ${String(total).padStart(2, "0")}`, 1114, 34, 104, 24, {
    size: 13,
    color: ACCENT_DARK,
    bold: true,
    face: MONO_FACE,
    align: "right",
    checkFit: false,
    role: "header",
  });
  addShape(slide, "rect", 64, 64, 1152, 2, INK, TRANSPARENT, 0, { slideNo, role: "header rule" });
  addShape(slide, "ellipse", 57, 57, 16, 16, ACCENT, INK, 2, { slideNo, role: "header marker" });
}

function addTitleBlock(slide, slideNo, title, subtitle = null, x = 64, y = 86, w = 780, dark = false) {
  const titleColor = dark ? PAPER : INK;
  const bodyColor = dark ? PAPER : GRAPHITE;
  addText(slide, slideNo, title, x, y, w, 142, {
    size: 40,
    color: titleColor,
    bold: true,
    face: TITLE_FACE,
    role: "title",
  });
  if (subtitle) {
    addText(slide, slideNo, subtitle, x + 2, y + 148, Math.min(w, 720), 70, {
      size: 19,
      color: bodyColor,
      face: BODY_FACE,
      role: "subtitle",
    });
  }
}

function addIconBadge(slide, slideNo, x, y, accent = ACCENT, kind = "signal") {
  addShape(slide, "ellipse", x, y, 54, 54, PAPER_96, INK, 1.2, { slideNo, role: "icon badge" });
  if (kind === "flow") {
    addShape(slide, "ellipse", x + 13, y + 18, 10, 10, accent, INK, 1, { slideNo, role: "icon glyph" });
    addShape(slide, "ellipse", x + 31, y + 27, 10, 10, accent, INK, 1, { slideNo, role: "icon glyph" });
    addShape(slide, "rect", x + 22, y + 25, 19, 3, INK, TRANSPARENT, 0, { slideNo, role: "icon glyph" });
  } else if (kind === "layers") {
    addShape(slide, "roundRect", x + 13, y + 15, 26, 13, accent, INK, 1, { slideNo, role: "icon glyph" });
    addShape(slide, "roundRect", x + 18, y + 24, 26, 13, GOLD, INK, 1, { slideNo, role: "icon glyph" });
    addShape(slide, "roundRect", x + 23, y + 33, 20, 10, CORAL, INK, 1, { slideNo, role: "icon glyph" });
  } else {
    addShape(slide, "rect", x + 16, y + 29, 6, 12, accent, TRANSPARENT, 0, { slideNo, role: "icon glyph" });
    addShape(slide, "rect", x + 25, y + 21, 6, 20, accent, TRANSPARENT, 0, { slideNo, role: "icon glyph" });
    addShape(slide, "rect", x + 34, y + 14, 6, 27, accent, TRANSPARENT, 0, { slideNo, role: "icon glyph" });
  }
}

function addCard(slide, slideNo, x, y, w, h, label, body, { accent = ACCENT, fill = PAPER_96, line = INK, iconKind = "signal" } = {}) {
  if (h < 156) {
    throw new Error(`Card is too short for editable pro-deck copy: height=${h.toFixed(1)}, minimum=156.`);
  }
  addShape(slide, "roundRect", x, y, w, h, fill, line, 1.2, { slideNo, role: `card panel: ${label}` });
  addShape(slide, "rect", x, y, 8, h, accent, TRANSPARENT, 0, { slideNo, role: `card accent: ${label}` });
  addIconBadge(slide, slideNo, x + 22, y + 24, accent, iconKind);
  addText(slide, slideNo, label, x + 88, y + 22, w - 108, 28, {
    size: 15,
    color: ACCENT_DARK,
    bold: true,
    face: MONO_FACE,
    role: "card label",
  });
  const wrapped = wrapText(body, Math.max(28, Math.floor(w / 13)));
  const bodyY = y + 86;
  const bodyH = h - (bodyY - y) - 22;
  if (bodyH < 54) {
    throw new Error(`Card body area is too short: height=${bodyH.toFixed(1)}, cardHeight=${h.toFixed(1)}, label=${JSON.stringify(label)}.`);
  }
  addText(slide, slideNo, wrapped, x + 24, bodyY, w - 48, bodyH, {
    size: 16,
    color: INK,
    face: BODY_FACE,
    role: `card body: ${label}`,
  });
}

function addMetricCard(slide, slideNo, x, y, w, h, metric, label, note = null, accent = ACCENT) {
  if (h < 132) {
    throw new Error(`Metric card is too short for editable pro-deck copy: height=${h.toFixed(1)}, minimum=132.`);
  }
  addShape(slide, "roundRect", x, y, w, h, PAPER_96, INK, 1.2, { slideNo, role: `metric panel: ${label}` });
  addShape(slide, "rect", x, y, w, 7, accent, TRANSPARENT, 0, { slideNo, role: `metric accent: ${label}` });
  addText(slide, slideNo, metric, x + 22, y + 24, w - 44, 54, {
    size: 34,
    color: INK,
    bold: true,
    face: TITLE_FACE,
    role: "metric value",
  });
  addText(slide, slideNo, label, x + 24, y + 82, w - 48, 38, {
    size: 16,
    color: GRAPHITE,
    face: BODY_FACE,
    role: "metric label",
  });
  if (note) {
    addText(slide, slideNo, note, x + 24, y + h - 42, w - 48, 22, {
      size: 10,
      color: MUTED,
      face: BODY_FACE,
      role: "metric note",
    });
  }
}

function addTag(slide, slideNo, text, x, y, w, { fill = WHITE, line = TRANSPARENT, color = INK } = {}) {
  addShape(slide, "roundRect", x, y, w, 34, fill, line, line === TRANSPARENT ? 0 : 1.1, { slideNo, role: `tag: ${text}` });
  addText(slide, slideNo, text, x + 14, y + 7, w - 28, 20, {
    size: 12,
    color,
    bold: true,
    face: MONO_FACE,
    align: "center",
    checkFit: false,
    role: "tag text",
  });
}

function bulletsToText(items) {
  return (items || []).map((item) => `• ${item}`).join("\n");
}

function addNotes(slide, body, sourceKeys) {
  const sourceLines = (sourceKeys || []).map((key) => `- ${SOURCES[key] || key}`).join("\n");
  slide.speakerNotes.setText(`${body || ""}\n\n[Sources]\n${sourceLines}`);
}

function addReferenceCaption(slide, slideNo) {
  addText(
    slide,
    slideNo,
    "FoodSprint • AI-assisted coding project • Flask, Jinja, SQLAlchemy, OpenStreetMap, and UPI QR workflow",
    64,
    674,
    1060,
    22,
    {
      size: 10,
      color: MUTED,
      face: BODY_FACE,
      checkFit: false,
      role: "caption",
    },
  );
}

async function slideCover(presentation) {
  const slideNo = 1;
  const data = SLIDES[0];
  const slide = presentation.slides.add();
  await addPlate(slide, slideNo);
  addShape(slide, "rect", 0, 0, W, H, "#FFF8F1", TRANSPARENT, 0, { slideNo, role: "cover base overlay" });
  addShape(slide, "ellipse", 842, 72, 350, 350, "#FFE2C4", TRANSPARENT, 0, { slideNo, role: "cover decorative circle" });
  addShape(slide, "ellipse", 1014, 294, 150, 150, "#EAF9F1", TRANSPARENT, 0, { slideNo, role: "cover decorative circle" });
  addShape(slide, "rect", 64, 86, 7, 455, ACCENT, TRANSPARENT, 0, { slideNo, role: "cover accent rule" });
  addText(slide, slideNo, data.kicker, 86, 88, 520, 26, {
    size: 13,
    color: ACCENT_DARK,
    bold: true,
    face: MONO_FACE,
    role: "kicker",
  });
  addText(slide, slideNo, data.title, 82, 130, 785, 184, {
    size: 48,
    color: INK,
    bold: true,
    face: TITLE_FACE,
    role: "cover title",
  });
  addText(slide, slideNo, data.subtitle, 86, 326, 610, 86, {
    size: 20,
    color: GRAPHITE,
    face: BODY_FACE,
    role: "cover subtitle",
  });
  addShape(slide, "roundRect", 86, 456, 474, 92, PAPER_96, INK, 1.2, { slideNo, role: "cover moment panel" });
  addText(slide, slideNo, data.moment || "Replace with core idea", 112, 478, 420, 40, {
    size: 21,
    color: INK,
    bold: true,
    face: TITLE_FACE,
    role: "cover moment",
  });
  addShape(slide, "roundRect", 756, 122, 434, 452, WHITE, INK, 1.2, { slideNo, role: "cover highlight panel" });
  addText(slide, slideNo, "Why this project matters", 790, 158, 300, 30, {
    size: 24,
    color: INK,
    bold: true,
    face: TITLE_FACE,
    role: "cover panel title",
  });
  addText(slide, slideNo, "It demonstrates full-stack development with AI-assisted iteration, review, and presentation support.", 790, 204, 332, 66, {
    size: 16,
    color: GRAPHITE,
    face: BODY_FACE,
    role: "cover panel subtitle",
  });
  addTag(slide, slideNo, "Flask + SQLAlchemy", 790, 294, 166, { fill: SOFT_ORANGE, color: ACCENT_DARK });
  addTag(slide, slideNo, "OpenStreetMap", 966, 294, 138, { fill: SOFT_GREEN, color: ACCENT_DARK });
  addTag(slide, slideNo, "UPI QR", 1112, 294, 78, { fill: SOFT_ORANGE, color: ACCENT_DARK });
  (data.highlights || []).slice(0, 3).forEach((item, index) => {
    addShape(slide, "roundRect", 790, 348 + index * 70, 366, 54, "#FFF9F3", "#F2D7B7", 1, { slideNo, role: `cover highlight ${index + 1}` });
    addText(slide, slideNo, item, 812, 364 + index * 70, 326, 22, {
      size: 14,
      color: INK,
      bold: true,
      face: BODY_FACE,
      checkFit: false,
      role: "cover highlight text",
    });
  });
  addReferenceCaption(slide, slideNo);
  addNotes(slide, data.notes, data.sources);
}

async function slideCards(presentation, idx) {
  const data = SLIDES[idx - 1];
  const slide = presentation.slides.add();
  await addPlate(slide, idx);
  addShape(slide, "rect", 0, 0, W, H, "#FFFFFFB8", TRANSPARENT, 0, { slideNo: idx, role: "content contrast overlay" });
  addHeader(slide, idx, data.kicker, idx, SLIDES.length);
  addTitleBlock(slide, idx, data.title, data.subtitle, 64, 86, 760);
  const cards = data.cards?.length
    ? data.cards
    : [
        ["Replace", "Add a specific, sourced point for this slide."],
        ["Author", "Use native PowerPoint chart objects for charts; use deterministic geometry for cards and callouts."],
        ["Verify", "Render previews, inspect them at readable size, and fix actionable layout issues within 3 total render loops."],
      ];
  const cols = Math.min(3, cards.length);
  const cardW = (1114 - (cols - 1) * 24) / cols;
  const iconKinds = ["signal", "flow", "layers"];
  for (let cardIdx = 0; cardIdx < cols; cardIdx += 1) {
    const [label, body] = cards[cardIdx];
    const x = 84 + cardIdx * (cardW + 24);
    addCard(slide, idx, x, 376, cardW, 236, label, body, { iconKind: iconKinds[cardIdx % iconKinds.length] });
  }
  addReferenceCaption(slide, idx);
  addNotes(slide, data.notes, data.sources);
}

async function slideMetrics(presentation, idx) {
  const data = SLIDES[idx - 1];
  const slide = presentation.slides.add();
  await addPlate(slide, idx);
  addShape(slide, "rect", 0, 0, W, H, "#FFFFFFBD", TRANSPARENT, 0, { slideNo: idx, role: "metrics contrast overlay" });
  addHeader(slide, idx, data.kicker, idx, SLIDES.length);
  addTitleBlock(slide, idx, data.title, data.subtitle, 64, 86, 700);
  const metrics = data.metrics || [
    ["00", "Replace metric", "Source"],
    ["00", "Replace metric", "Source"],
    ["00", "Replace metric", "Source"],
  ];
  const accents = [ACCENT, GOLD, CORAL];
  for (let metricIdx = 0; metricIdx < Math.min(3, metrics.length); metricIdx += 1) {
    const [metric, label, note] = metrics[metricIdx];
    addMetricCard(slide, idx, 92 + metricIdx * 370, 404, 330, 174, metric, label, note, accents[metricIdx % accents.length]);
  }
  addReferenceCaption(slide, idx);
  addNotes(slide, data.notes, data.sources);
}

async function slideCodeExample(presentation, idx) {
  const data = SLIDES[idx - 1];
  const slide = presentation.slides.add();
  await addPlate(slide, idx);
  addShape(slide, "rect", 0, 0, W, H, "#FFF8F1", TRANSPARENT, 0, { slideNo: idx, role: "code slide base" });
  addHeader(slide, idx, data.kicker, idx, SLIDES.length);
  addTitleBlock(slide, idx, data.title, data.subtitle, 64, 86, 494);

  addShape(slide, "roundRect", 64, 312, 486, 94, WHITE, "#E7D5C2", 1.1, { slideNo: idx, role: "prompt panel" });
  addText(slide, idx, "Prompt used", 90, 334, 150, 22, {
    size: 13,
    color: ACCENT_DARK,
    bold: true,
    face: MONO_FACE,
    checkFit: false,
    role: "prompt label",
  });
  addText(slide, idx, data.promptText, 90, 364, 430, 24, {
    size: 17,
    color: INK,
    bold: true,
    face: BODY_FACE,
    checkFit: false,
    role: "prompt text",
  });

  addShape(slide, "roundRect", 64, 434, 486, 196, WHITE, "#E7D5C2", 1.1, { slideNo: idx, role: "takeaways panel" });
  addText(slide, idx, "What this shows", 90, 458, 180, 22, {
    size: 13,
    color: ACCENT_DARK,
    bold: true,
    face: MONO_FACE,
    checkFit: false,
    role: "takeaways label",
  });
  addText(slide, idx, bulletsToText(data.takeaways), 90, 492, 424, 112, {
    size: 16,
    color: INK,
    face: BODY_FACE,
    role: "takeaways text",
  });

  addShape(slide, "roundRect", 584, 118, 632, 512, NAVY, NAVY_LINE, 1.2, { slideNo: idx, role: "code image frame" });
  if (data.imagePath && (await pathExists(data.imagePath))) {
    await addImage(
      slide,
      idx,
      { path: data.imagePath, fit: "contain", alt: `${data.title} code image` },
      { left: 608, top: 142, width: 584, height: 464 },
      "code example image",
      data.imagePath,
    );
  }
  addReferenceCaption(slide, idx);
  addNotes(slide, data.notes, data.sources);
}

async function slideCommands(presentation, idx) {
  const data = SLIDES[idx - 1];
  const slide = presentation.slides.add();
  await addPlate(slide, idx);
  addShape(slide, "rect", 0, 0, W, H, "#FFF8F1", TRANSPARENT, 0, { slideNo: idx, role: "commands base" });
  addHeader(slide, idx, data.kicker, idx, SLIDES.length);
  addTitleBlock(slide, idx, data.title, data.subtitle, 64, 86, 720);

  const commandText = String(data.commandText || "").replaceAll("\\n", "\n");
  addShape(slide, "roundRect", 64, 320, 714, 236, NAVY, NAVY_LINE, 1.2, { slideNo: idx, role: "terminal panel" });
  addText(slide, idx, commandText, 94, 350, 652, 176, {
    size: 14,
    color: "#E5E7EB",
    face: MONO_FACE,
    role: "terminal commands",
  });

  [
    { y: 320, accent: ACCENT, title: data.cards[0][0], body: data.cards[0][1] },
    { y: 430, accent: GOLD, title: data.cards[1][0], body: data.cards[1][1] },
    { y: 540, accent: CORAL, title: data.cards[2][0], body: data.cards[2][1] },
  ].forEach((item, index) => {
    addShape(slide, "roundRect", 820, item.y, 376, 96, WHITE, "#E7D5C2", 1.1, { slideNo: idx, role: `command note ${index + 1}` });
    addShape(slide, "rect", 820, item.y, 8, 96, item.accent, TRANSPARENT, 0, { slideNo: idx, role: `command note accent ${index + 1}` });
    addText(slide, idx, item.title, 844, item.y + 14, 312, 22, {
      size: 16,
      color: INK,
      bold: true,
      face: BODY_FACE,
      checkFit: false,
      role: "command note title",
    });
    addText(slide, idx, item.body, 844, item.y + 40, 322, 30, {
      size: 13,
      color: GRAPHITE,
      face: BODY_FACE,
      role: "command note body",
    });
  });

  addReferenceCaption(slide, idx);
  addNotes(slide, data.notes, data.sources);
}

async function createDeck() {
  await ensureDirs();
  if (!SLIDES.length) {
    throw new Error("SLIDES must contain at least one slide.");
  }
  const presentation = Presentation.create({ slideSize: { width: W, height: H } });
  for (let idx = 1; idx <= SLIDES.length; idx += 1) {
    const data = SLIDES[idx - 1];
    if (idx === 1 || data.layout === "cover") {
      await slideCover(presentation);
    } else if (data.layout === "metrics") {
      await slideMetrics(presentation, idx);
    } else if (data.layout === "code") {
      await slideCodeExample(presentation, idx);
    } else if (data.layout === "commands") {
      await slideCommands(presentation, idx);
    } else {
      await slideCards(presentation, idx);
    }
  }
  return presentation;
}

async function saveBlobToFile(blob, filePath) {
  const bytes = new Uint8Array(await blob.arrayBuffer());
  await fs.writeFile(filePath, bytes);
}

async function writeInspectArtifact(presentation) {
  inspectRecords.unshift({
    kind: "deck",
    id: DECK_ID,
    slideCount: presentation.slides.count,
    slideSize: { width: W, height: H },
  });
  presentation.slides.items.forEach((slide, index) => {
    inspectRecords.splice(index + 1, 0, {
      kind: "slide",
      slide: index + 1,
      id: slide?.id || `slide-${index + 1}`,
    });
  });
  const lines = inspectRecords.map((record) => JSON.stringify(record)).join("\n") + "\n";
  await fs.writeFile(INSPECT_PATH, lines, "utf8");
}

async function currentRenderLoopCount() {
  const logPath = path.join(VERIFICATION_DIR, "render_verify_loops.ndjson");
  if (!(await pathExists(logPath))) return 0;
  const previous = await fs.readFile(logPath, "utf8");
  return previous.split(/\r?\n/).filter((line) => line.trim()).length;
}

async function nextRenderLoopNumber() {
  return (await currentRenderLoopCount()) + 1;
}

async function appendRenderVerifyLoop(presentation, previewPaths, pptxPath) {
  const logPath = path.join(VERIFICATION_DIR, "render_verify_loops.ndjson");
  const priorCount = await currentRenderLoopCount();
  const record = {
    kind: "render_verify_loop",
    deckId: DECK_ID,
    loop: priorCount + 1,
    maxLoops: MAX_RENDER_VERIFY_LOOPS,
    capReached: priorCount + 1 >= MAX_RENDER_VERIFY_LOOPS,
    timestamp: new Date().toISOString(),
    slideCount: presentation.slides.count,
    previewCount: previewPaths.length,
    previewDir: PREVIEW_DIR,
    inspectPath: INSPECT_PATH,
    pptxPath,
  };
  await fs.appendFile(logPath, JSON.stringify(record) + "\n", "utf8");
  return record;
}

async function verifyAndExport(presentation) {
  await ensureDirs();
  const nextLoop = await nextRenderLoopNumber();
  if (nextLoop > MAX_RENDER_VERIFY_LOOPS) {
    throw new Error(
      `Render/verify/fix loop cap reached: ${MAX_RENDER_VERIFY_LOOPS} total renders are allowed. ` +
        "Do not rerender; note any remaining visual issues in the final response.",
    );
  }
  await writeInspectArtifact(presentation);
  const previewPaths = [];
  for (let idx = 0; idx < presentation.slides.items.length; idx += 1) {
    const slide = presentation.slides.items[idx];
    const preview = await presentation.export({ slide, format: "png", scale: 1 });
    const previewPath = path.join(PREVIEW_DIR, `slide-${String(idx + 1).padStart(2, "0")}.png`);
    await saveBlobToFile(preview, previewPath);
    previewPaths.push(previewPath);
  }
  const pptxBlob = await PresentationFile.exportPptx(presentation);
  const pptxPath = path.join(OUT_DIR, "output.pptx");
  await pptxBlob.save(pptxPath);
  const loopRecord = await appendRenderVerifyLoop(presentation, previewPaths, pptxPath);
  return { pptxPath, loopRecord };
}

const presentation = await createDeck();
const result = await verifyAndExport(presentation);
console.log(result.pptxPath);
