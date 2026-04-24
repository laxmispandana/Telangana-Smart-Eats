const fs = await import("node:fs/promises");
const path = await import("node:path");
const { Presentation, PresentationFile } = await import("@oai/artifact-tool");

const W = 1280;
const H = 720;

const DECK_ID = "foodsprint-evaluation-ppt";
const OUT_DIR = "C:\\Users\\spand\\OneDrive\\Documents\\New project\\outputs\\foodsprint-evaluation-ppt";
const SCRATCH_DIR = path.resolve("tmp", "slides", DECK_ID);
const PREVIEW_DIR = path.join(SCRATCH_DIR, "preview");
const VERIFICATION_DIR = path.join(SCRATCH_DIR, "verification");
const INSPECT_PATH = path.join(SCRATCH_DIR, "inspect.ndjson");

const ASSET_DIR = "C:\\Users\\spand\\OneDrive\\Documents\\New project\\tmp\\slides\\foodsprint-evaluation-ppt\\assets";
const PROOF_DIR = "C:\\Users\\spand\\OneDrive\\Documents\\New project\\tmp\\slides\\foodsprint-ai-assisted-project\\assets";

const INK = "#141414";
const GRAPHITE = "#374151";
const MUTED = "#6B7280";
const PAPER = "#F8F4ED";
const PAPER_SOFT = "#FCFAF6";
const WHITE = "#FFFFFF";
const ACCENT = "#FC8019";
const ACCENT_DARK = "#A74F0E";
const GREEN = "#27C47D";
const CORAL = "#E86F5B";
const NAVY = "#11192F";
const NAVY_LINE = "#22304A";
const LINE = "#DFCDBA";
const TRANSPARENT = "#00000000";

const TITLE_FACE = "Segoe UI";
const BODY_FACE = "Segoe UI";
const MONO_FACE = "Consolas";

const SOURCES = {
  repo: "FoodSprint local repository files: README.md, app/routes.py, app/models.py, app/templates/index.html, app/services/data_seed.py, app/services/image_utils.py.",
  docs: "Official framework and platform documentation for Flask, SQLAlchemy, Leaflet, OpenStreetMap, Overpass API, and Playwright.",
  conversation: "Recorded prompts from the current AI-assisted work session.",
};

const SLIDES = [
  {
    layout: "cover",
    kicker: "SLIDE 1: TITLE AND TEAM DETAILS",
    title: "FoodSprint",
    subtitle: "AI-assisted food ordering and restaurant discovery web application built with Flask for Telangana users.",
    moment: "Replace the team placeholders with your actual details before presentation",
    details: [
      "Student 1: [Add Name and Roll Number]",
      "Student 2: [Add Name and Roll Number]",
      "Guide / Section: [Add Faculty Name or Class Details]",
    ],
    notes: "Introduce the project name and team details. Update the placeholders before presenting.",
    sources: ["repo"],
  },
  {
    layout: "cards",
    kicker: "SLIDE 2: INTRODUCTION OF PROJECT",
    title: "Introduction of project",
    subtitle: "FoodSprint is a full-stack restaurant discovery and ordering application with AI-assisted development support.",
    cards: [
      ["What it is", "FoodSprint helps users discover restaurants, browse menus, add items to cart, pay using UPI QR, and track their orders."],
      ["Where it helps", "The project focuses on Telangana city-based restaurant discovery with map support, dietary suggestions, and nearby search."],
      ["Why it stands out", "It also includes admin and staff dashboards, making the project useful for customers as well as restaurant operations."],
    ],
    notes: "Explain the app in simple words before discussing features and tools.",
    sources: ["repo"],
  },
  {
    layout: "cards4",
    kicker: "SLIDE 3: OBJECTIVES",
    title: "Objectives",
    subtitle: "The project was designed to solve both customer-side and operations-side food ordering needs.",
    cards: [
      ["Restaurant discovery", "Allow users to find restaurants by city, nearby distance, map view, rating, and food preference."],
      ["Ordering workflow", "Provide a complete flow from menu browsing and cart management to checkout and order tracking."],
      ["Diet support", "Recommend food options for weight loss, muscle gain, balanced diet, and vegetarian preference."],
      ["Operational control", "Enable admin and staff users to manage payment settings, staff accounts, and order status updates."],
    ],
    notes: "Mention that the project is both user-facing and operations-aware.",
    sources: ["repo"],
  },
  {
    layout: "cards4",
    kicker: "SLIDE 4: STAKEHOLDERS",
    title: "Stakeholders",
    subtitle: "FoodSprint serves multiple kinds of users and project participants.",
    cards: [
      ["Customers", "They search restaurants, explore menus, place orders, make payments, and track deliveries."],
      ["Admin", "The admin manages staff accounts, configures UPI payment details, and monitors customer reviews and orders."],
      ["Staff", "Staff members update order status step by step from placed to delivered."],
      ["Developers and evaluators", "The project team builds and improves the product, while faculty reviewers evaluate functionality, design, and AI usage."],
    ],
    notes: "Explain the role of each stakeholder clearly.",
    sources: ["repo"],
  },
  {
    layout: "cards4",
    kicker: "SLIDE 5: PROGRAMMING LANGUAGES, TOOLS, AND SOFTWARE",
    title: "Programming languages, tools, and software",
    subtitle: "FoodSprint combines backend, frontend, database, mapping, and AI-assisted tooling.",
    cards: [
      ["Languages", "Python, HTML, CSS, JavaScript, SQL concepts, and Jinja templating were used to build the application."],
      ["Frameworks and libraries", "Flask, SQLAlchemy, Flask-Migrate, Leaflet, OpenStreetMap APIs, Overpass API, and qrcode support the app features."],
      ["Software tools", "Git, GitHub, Docker, Railway or Render-ready config, and browser-based testing were used during development."],
      ["AI tools", "OpenAI Codex or ChatGPT style assistance was used for prompt-driven coding, debugging, documentation, and presentation support."],
    ],
    notes: "Mention AI tools explicitly because they are part of the evaluation checklist.",
    sources: ["repo", "docs", "conversation"],
  },
  {
    layout: "promptlist",
    kicker: "SLIDE 6: ALL PROMPTS USED TO GENERATE THE CODES",
    title: "Recorded prompts used in the AI-assisted project phase",
    subtitle: "These are the prompts captured in the current documented session. Add any earlier project prompts if you used more before this session.",
    promptLines: [
      "i want to update redme in github aboutc current features",
      "what shold i need to do now deploy or anythhing",
      "some picures are not prper in the wesite add",
      "prepare a ppt for me and also add the images off code along with propmt above code as #",
      "For the project evaluation, we will be verifying ... send me ppt i do",
    ],
    notes: "Say clearly that these are the recorded prompts from the current session.",
    sources: ["conversation"],
  },
  {
    layout: "flow",
    kicker: "SLIDE 7: WORK FLOW CHART",
    title: "Workflow of the FoodSprint application",
    subtitle: "The application follows a clear end-to-end workflow from discovery to delivery.",
    flowSteps: [
      "User opens FoodSprint",
      "Find restaurants using search, city, and map filters",
      "View restaurant menu and add items to cart",
      "Proceed to checkout and generate UPI QR",
      "Confirm payment and create order",
      "Track order status in the app",
      "Admin and staff update delivery progress",
    ],
    notes: "Walk through the user journey step by step.",
    sources: ["repo"],
  },
  {
    layout: "frontend",
    kicker: "SLIDE 8: FRONT-END VIEW",
    title: "Front-end view of the web application",
    subtitle: "The homepage shows the project branding, nearby restaurant discovery, filters, and restaurant cards.",
    imagePath: `${ASSET_DIR}\\frontend_home_crop.png`,
    urlText: "Demo URL in this workspace: http://127.0.0.1:5000   |   Replace with deployed URL if available",
    notes: "Point to the hero section, nearby map section, and restaurant listing as frontend evidence.",
    sources: ["repo", "docs"],
  },
  {
    layout: "proof",
    kicker: "SLIDE 9: PROOF OF PROMPTS GENERATING CODES",
    title: "Proof of prompts generating project artifacts",
    subtitle: "These screenshots connect the prompt text directly to repository changes and code-related outputs.",
    imageA: `${PROOF_DIR}\\readme_prompt.png`,
    imageB: `${PROOF_DIR}\\image_prompt.png`,
    proofNotes: [
      "README update prompt led to a repo-aware documentation rewrite.",
      "Image quality prompt led to investigation of the image mapping service.",
    ],
    notes: "Use this slide as evidence that prompts were connected to project work.",
    sources: ["conversation", "repo"],
  },
  {
    layout: "references",
    kicker: "SLIDE 10: REFERENCES",
    title: "References",
    subtitle: "The project uses official framework documentation, mapping sources, and repository artifacts.",
    leftRefs: [
      "Flask documentation - https://flask.palletsprojects.com/",
      "SQLAlchemy documentation - https://docs.sqlalchemy.org/",
      "Leaflet documentation - https://leafletjs.com/",
      "OpenStreetMap - https://www.openstreetmap.org/",
    ],
    rightRefs: [
      "Overpass API - https://overpass-api.de/",
      "Playwright - https://playwright.dev/",
      "FoodSprint repository files and screenshots used in this presentation",
      "OpenAI Codex or ChatGPT assistance used for AI-assisted coding tasks",
    ],
    notes: "Keep this slide readable and concise.",
    sources: ["repo", "docs", "conversation"],
  },
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
  return bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
}

async function normalizeImageConfig(config) {
  if (!config.path) return config;
  const { path: imagePath, ...rest } = config;
  return { ...rest, blob: await readImageBlob(imagePath) };
}

async function ensureDirs() {
  await fs.mkdir(OUT_DIR, { recursive: true });
  await fs.mkdir(SCRATCH_DIR, { recursive: true });
  await fs.mkdir(PREVIEW_DIR, { recursive: true });
  await fs.mkdir(VERIFICATION_DIR, { recursive: true });
}

function lineConfig(fill = TRANSPARENT, width = 0) {
  return { style: "solid", fill, width };
}

function normalizeText(text) {
  if (Array.isArray(text)) return text.map((item) => String(item ?? "")).join("\n");
  return String(text ?? "");
}

function textLineCount(text) {
  const value = normalizeText(text);
  if (!value.trim()) return 0;
  return Math.max(1, value.split(/\n/).length);
}

function requiredTextHeight(text, fontSize, lineHeight = 1.18, minHeight = 8) {
  const lines = textLineCount(text);
  if (lines === 0) return minHeight;
  return Math.max(minHeight, lines * fontSize * lineHeight);
}

function assertTextFits(text, boxHeight, fontSize, role = "text") {
  const required = requiredTextHeight(text, fontSize);
  const tolerance = Math.max(2, fontSize * 0.08);
  if (normalizeText(text).trim() && boxHeight + tolerance < required) {
    throw new Error(`${role} text box is too short: height=${boxHeight.toFixed(1)}, required>=${required.toFixed(1)}, lines=${textLineCount(text)}`);
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
  if (current) lines.push(current);
  return lines.join("\n");
}

function recordText(slideNo, role, text, x, y, w, h) {
  inspectRecords.push({
    kind: "textbox",
    slide: slideNo,
    role,
    text: normalizeText(text),
    textLines: textLineCount(text),
    bbox: [x, y, w, h],
  });
}

function recordImage(slideNo, role, imagePath, x, y, w, h) {
  inspectRecords.push({
    kind: "image",
    slide: slideNo,
    role,
    path: imagePath,
    bbox: [x, y, w, h],
  });
}

function addShape(slide, geometry, x, y, w, h, fill = TRANSPARENT, line = TRANSPARENT, lineWidth = 0) {
  return slide.shapes.add({
    geometry,
    position: { left: x, top: y, width: w, height: h },
    fill,
    line: lineConfig(line, lineWidth),
  });
}

function addText(slide, slideNo, text, x, y, w, h, options = {}) {
  const {
    size = 22,
    color = INK,
    bold = false,
    face = BODY_FACE,
    align = "left",
    valign = "top",
    fill = TRANSPARENT,
    line = TRANSPARENT,
    lineWidth = 0,
    role = "text",
    checkFit = true,
  } = options;

  if (checkFit) assertTextFits(text, h, size, role);
  const box = addShape(slide, "rect", x, y, w, h, fill, line, lineWidth);
  box.text = text;
  box.text.fontSize = size;
  box.text.color = color;
  box.text.bold = Boolean(bold);
  box.text.alignment = align;
  box.text.verticalAlignment = valign;
  box.text.typeface = face;
  box.text.insets = { left: 0, right: 0, top: 0, bottom: 0 };
  recordText(slideNo, role, text, x, y, w, h);
  return box;
}

async function addImage(slide, slideNo, config, position, role, sourcePath) {
  const image = slide.images.add(await normalizeImageConfig(config));
  image.position = position;
  recordImage(slideNo, role, sourcePath || config.path || "inline", position.left, position.top, position.width, position.height);
  return image;
}

function addHeader(slide, slideNo, kicker, idx, total) {
  addText(slide, slideNo, String(kicker || "").toUpperCase(), 64, 34, 680, 24, {
    size: 13,
    color: ACCENT_DARK,
    bold: true,
    face: MONO_FACE,
    checkFit: false,
    role: "header",
  });
  addText(slide, slideNo, `${String(idx).padStart(2, "0")} / ${String(total).padStart(2, "0")}`, 1112, 34, 104, 24, {
    size: 13,
    color: ACCENT_DARK,
    bold: true,
    face: MONO_FACE,
    align: "right",
    checkFit: false,
    role: "header index",
  });
  addShape(slide, "rect", 64, 64, 1152, 2, INK, TRANSPARENT, 0);
  addShape(slide, "ellipse", 57, 57, 16, 16, ACCENT, INK, 2);
}

function addTitleBlock(slide, slideNo, title, subtitle, x = 64, y = 86, w = 840) {
  addText(slide, slideNo, title, x, y, w, 118, {
    size: 44,
    color: INK,
    bold: true,
    face: TITLE_FACE,
    role: "title",
  });
  if (subtitle) {
    addText(slide, slideNo, subtitle, x + 2, y + 144, Math.min(w, 940), 64, {
      size: 17,
      color: GRAPHITE,
      face: BODY_FACE,
      role: "subtitle",
    });
  }
}

function addIconBadge(slide, x, y, accent = ACCENT, kind = "signal") {
  addShape(slide, "ellipse", x, y, 52, 52, PAPER_SOFT, INK, 1.1);
  if (kind === "flow") {
    addShape(slide, "ellipse", x + 14, y + 20, 9, 9, accent, INK, 1);
    addShape(slide, "ellipse", x + 31, y + 29, 9, 9, accent, INK, 1);
    addShape(slide, "rect", x + 22, y + 27, 18, 3, INK, TRANSPARENT, 0);
  } else if (kind === "layers") {
    addShape(slide, "roundRect", x + 13, y + 14, 25, 12, accent, INK, 1);
    addShape(slide, "roundRect", x + 18, y + 23, 25, 12, GREEN, INK, 1);
    addShape(slide, "roundRect", x + 23, y + 32, 18, 9, CORAL, INK, 1);
  } else {
    addShape(slide, "rect", x + 16, y + 28, 6, 12, accent, TRANSPARENT, 0);
    addShape(slide, "rect", x + 25, y + 20, 6, 20, accent, TRANSPARENT, 0);
    addShape(slide, "rect", x + 34, y + 13, 6, 27, accent, TRANSPARENT, 0);
  }
}

function addCard(slide, slideNo, x, y, w, h, label, body, options = {}) {
  const { accent = ACCENT, iconKind = "signal" } = options;
  addShape(slide, "roundRect", x, y, w, h, WHITE, LINE, 1.1);
  addShape(slide, "rect", x, y, 8, h, accent, TRANSPARENT, 0);
  addIconBadge(slide, x + 20, y + 18, accent, iconKind);
  addText(slide, slideNo, label, x + 86, y + 24, w - 106, 24, {
    size: 15,
    color: ACCENT_DARK,
    bold: true,
    face: MONO_FACE,
    checkFit: false,
    role: "card label",
  });
  const wrapped = wrapText(body, Math.max(26, Math.floor(w / 13)));
  addText(slide, slideNo, wrapped, x + 24, y + 82, w - 48, h - 102, {
    size: 14,
    color: INK,
    face: BODY_FACE,
    role: `card body: ${label}`,
  });
}

function addTag(slide, slideNo, text, x, y, w, fill = WHITE) {
  addShape(slide, "roundRect", x, y, w, 34, fill, LINE, 1);
  addText(slide, slideNo, text, x + 14, y + 7, w - 28, 18, {
    size: 12,
    color: ACCENT_DARK,
    bold: true,
    face: MONO_FACE,
    align: "center",
    checkFit: false,
    role: "tag",
  });
}

function bulletsToText(items) {
  return (items || []).map((item) => `- ${item}`).join("\n");
}

function addNotes(slide, body, sourceKeys) {
  const sourceLines = (sourceKeys || []).map((key) => `- ${SOURCES[key] || key}`).join("\n");
  slide.speakerNotes.setText(`${body || ""}\n\n[Sources]\n${sourceLines}`);
}

function addReferenceCaption(slide, slideNo) {
  addText(slide, slideNo, "FoodSprint evaluation deck • AI-assisted coding project • Flask, SQLAlchemy, Leaflet, OpenStreetMap, and UPI QR", 64, 674, 1088, 18, {
    size: 10,
    color: MUTED,
    face: BODY_FACE,
    checkFit: false,
    role: "caption",
  });
}

async function slideCover(presentation) {
  const slideNo = 1;
  const data = SLIDES[0];
  const slide = presentation.slides.add();
  slide.background.fill = PAPER;
  addShape(slide, "ellipse", 850, 72, 340, 340, "#FFE2C4", TRANSPARENT, 0);
  addShape(slide, "ellipse", 1020, 296, 148, 148, "#EAF9F1", TRANSPARENT, 0);
  addShape(slide, "rect", 64, 86, 7, 455, ACCENT, TRANSPARENT, 0);
  addText(slide, slideNo, data.kicker, 86, 88, 540, 24, {
    size: 13,
    color: ACCENT_DARK,
    bold: true,
    face: MONO_FACE,
    checkFit: false,
    role: "kicker",
  });
  addText(slide, slideNo, data.title, 82, 132, 620, 110, {
    size: 48,
    color: INK,
    bold: true,
    face: TITLE_FACE,
    role: "cover title",
  });
  addText(slide, slideNo, data.subtitle, 86, 290, 620, 88, {
    size: 19,
    color: GRAPHITE,
    face: BODY_FACE,
    role: "cover subtitle",
  });
  addShape(slide, "roundRect", 86, 454, 492, 92, PAPER_SOFT, INK, 1.1);
  addText(slide, slideNo, data.moment, 110, 478, 446, 36, {
    size: 18,
    color: INK,
    bold: true,
    face: TITLE_FACE,
    role: "cover moment",
  });
  addShape(slide, "roundRect", 756, 120, 434, 454, WHITE, INK, 1.1);
  addText(slide, slideNo, "Team details", 790, 156, 280, 28, {
    size: 24,
    color: INK,
    bold: true,
    face: TITLE_FACE,
    role: "cover panel title",
  });
  addText(slide, slideNo, "Fill in your student names, roll numbers, class, and faculty details before your final presentation.", 790, 200, 340, 62, {
    size: 15,
    color: GRAPHITE,
    face: BODY_FACE,
    role: "cover panel subtitle",
  });
  addTag(slide, slideNo, "Project type: Web application", 790, 286, 220, "#FFF1E4");
  addTag(slide, slideNo, "Theme: AI-assisted coding", 1020, 286, 170, "#EAF9F1");
  (data.details || []).slice(0, 3).forEach((item, index) => {
    addShape(slide, "roundRect", 790, 344 + index * 74, 366, 58, "#FFF9F3", "#F2D7B7", 1);
    addText(slide, slideNo, item, 812, 364 + index * 74, 326, 24, {
      size: 14,
      color: INK,
      bold: true,
      face: BODY_FACE,
      checkFit: false,
      role: "team detail",
    });
  });
  addReferenceCaption(slide, slideNo);
  addNotes(slide, data.notes, data.sources);
}

async function slideCards(presentation, idx) {
  const data = SLIDES[idx - 1];
  const slide = presentation.slides.add();
  slide.background.fill = PAPER;
  addHeader(slide, idx, data.kicker, idx, SLIDES.length);
  addTitleBlock(slide, idx, data.title, data.subtitle, 64, 86, 920);
  const cards = data.cards || [];
  const iconKinds = ["signal", "flow", "layers", "signal"];

  if (cards.length === 4 || data.layout === "cards4") {
    const positions = [
      [84, 312],
      [656, 312],
      [84, 486],
      [656, 486],
    ];
    cards.slice(0, 4).forEach((card, i) => {
      addCard(slide, idx, positions[i][0], positions[i][1], 540, 168, card[0], card[1], { accent: i % 2 === 0 ? ACCENT : GREEN, iconKind: iconKinds[i] });
    });
  } else {
    const cardW = (1114 - (cards.length - 1) * 24) / Math.max(1, cards.length);
    cards.forEach((card, i) => {
      addCard(slide, idx, 84 + i * (cardW + 24), 384, cardW, 220, card[0], card[1], { accent: i === 1 ? GREEN : i === 2 ? CORAL : ACCENT, iconKind: iconKinds[i] });
    });
  }

  addReferenceCaption(slide, idx);
  addNotes(slide, data.notes, data.sources);
}

async function slidePromptList(presentation, idx) {
  const data = SLIDES[idx - 1];
  const slide = presentation.slides.add();
  slide.background.fill = PAPER;
  addHeader(slide, idx, data.kicker, idx, SLIDES.length);
  addTitleBlock(slide, idx, data.title, data.subtitle, 64, 86, 1040);
  addShape(slide, "roundRect", 64, 288, 1152, 332, NAVY, NAVY_LINE, 1.2);
  addText(slide, idx, (data.promptLines || []).map((line, i) => `${i + 1}. ${line}`).join("\n"), 96, 322, 1088, 252, {
    size: 18,
    color: "#E5E7EB",
    face: MONO_FACE,
    role: "prompt list",
  });
  addText(slide, idx, "Tip: add any earlier prompts you used before this recorded session so the slide fully matches your project history.", 64, 636, 1020, 18, {
    size: 11,
    color: MUTED,
    face: BODY_FACE,
    checkFit: false,
    role: "prompt tip",
  });
  addReferenceCaption(slide, idx);
  addNotes(slide, data.notes, data.sources);
}

async function slideFlow(presentation, idx) {
  const data = SLIDES[idx - 1];
  const slide = presentation.slides.add();
  slide.background.fill = PAPER;
  addHeader(slide, idx, data.kicker, idx, SLIDES.length);
  addTitleBlock(slide, idx, data.title, data.subtitle, 64, 86, 920);

  const steps = data.flowSteps || [];
  const boxes = [
    [76, 300],
    [358, 300],
    [640, 300],
    [922, 300],
    [922, 470],
    [640, 470],
    [358, 470],
  ];

  steps.slice(0, 7).forEach((step, i) => {
    const [x, y] = boxes[i];
    addShape(slide, "roundRect", x, y, 210, 82, WHITE, LINE, 1.1);
    addText(slide, idx, step, x + 18, y + 18, 174, 42, {
      size: 13,
      color: INK,
      bold: true,
      face: BODY_FACE,
      role: "flow step",
    });
  });

  addText(slide, idx, "->", 302, 324, 40, 24, { size: 24, color: ACCENT, bold: true, face: MONO_FACE, checkFit: false, role: "flow arrow" });
  addText(slide, idx, "->", 584, 324, 40, 24, { size: 24, color: ACCENT, bold: true, face: MONO_FACE, checkFit: false, role: "flow arrow" });
  addText(slide, idx, "->", 866, 324, 40, 24, { size: 24, color: ACCENT, bold: true, face: MONO_FACE, checkFit: false, role: "flow arrow" });
  addText(slide, idx, "v", 1012, 408, 20, 24, { size: 24, color: ACCENT, bold: true, face: MONO_FACE, checkFit: false, role: "flow arrow" });
  addText(slide, idx, "<-", 866, 494, 40, 24, { size: 24, color: ACCENT, bold: true, face: MONO_FACE, checkFit: false, role: "flow arrow" });
  addText(slide, idx, "<-", 584, 494, 40, 24, { size: 24, color: ACCENT, bold: true, face: MONO_FACE, checkFit: false, role: "flow arrow" });

  addReferenceCaption(slide, idx);
  addNotes(slide, data.notes, data.sources);
}

async function slideFrontend(presentation, idx) {
  const data = SLIDES[idx - 1];
  const slide = presentation.slides.add();
  slide.background.fill = PAPER;
  addHeader(slide, idx, data.kicker, idx, SLIDES.length);
  addTitleBlock(slide, idx, data.title, data.subtitle, 64, 86, 920);
  addShape(slide, "roundRect", 74, 252, 1132, 348, WHITE, LINE, 1.1);
  if (data.imagePath && (await pathExists(data.imagePath))) {
    await addImage(slide, idx, { path: data.imagePath, fit: "contain", alt: "FoodSprint frontend screenshot" }, { left: 90, top: 270, width: 1100, height: 312 }, "frontend screenshot", data.imagePath);
  }
  addShape(slide, "roundRect", 92, 616, 1096, 42, "#FFF1E4", LINE, 1);
  addText(slide, idx, data.urlText, 118, 628, 1046, 16, {
    size: 12,
    color: ACCENT_DARK,
    face: MONO_FACE,
    checkFit: false,
    role: "frontend url",
  });
  addReferenceCaption(slide, idx);
  addNotes(slide, data.notes, data.sources);
}

async function slideProof(presentation, idx) {
  const data = SLIDES[idx - 1];
  const slide = presentation.slides.add();
  slide.background.fill = PAPER;
  addHeader(slide, idx, data.kicker, idx, SLIDES.length);
  addTitleBlock(slide, idx, data.title, data.subtitle, 64, 86, 1040);
  addShape(slide, "roundRect", 64, 286, 554, 302, NAVY, NAVY_LINE, 1.2);
  addShape(slide, "roundRect", 662, 286, 554, 302, NAVY, NAVY_LINE, 1.2);
  if (data.imageA && (await pathExists(data.imageA))) {
    await addImage(slide, idx, { path: data.imageA, fit: "contain", alt: "Proof screenshot A" }, { left: 80, top: 302, width: 522, height: 270 }, "proof a", data.imageA);
  }
  if (data.imageB && (await pathExists(data.imageB))) {
    await addImage(slide, idx, { path: data.imageB, fit: "contain", alt: "Proof screenshot B" }, { left: 678, top: 302, width: 522, height: 270 }, "proof b", data.imageB);
  }
  addText(slide, idx, bulletsToText(data.proofNotes), 64, 612, 1040, 38, {
    size: 14,
    color: GRAPHITE,
    face: BODY_FACE,
    role: "proof notes",
  });
  addReferenceCaption(slide, idx);
  addNotes(slide, data.notes, data.sources);
}

async function slideReferences(presentation, idx) {
  const data = SLIDES[idx - 1];
  const slide = presentation.slides.add();
  slide.background.fill = PAPER;
  addHeader(slide, idx, data.kicker, idx, SLIDES.length);
  addTitleBlock(slide, idx, data.title, data.subtitle, 64, 86, 1040);
  addShape(slide, "roundRect", 64, 286, 548, 320, WHITE, LINE, 1.1);
  addShape(slide, "roundRect", 668, 286, 548, 320, WHITE, LINE, 1.1);
  addText(slide, idx, bulletsToText(data.leftRefs), 92, 320, 492, 242, {
    size: 14,
    color: INK,
    face: BODY_FACE,
    role: "references left",
  });
  addText(slide, idx, bulletsToText(data.rightRefs), 696, 320, 492, 242, {
    size: 14,
    color: INK,
    face: BODY_FACE,
    role: "references right",
  });
  addReferenceCaption(slide, idx);
  addNotes(slide, data.notes, data.sources);
}

async function createDeck() {
  await ensureDirs();
  const presentation = Presentation.create({ slideSize: { width: W, height: H } });
  for (let idx = 1; idx <= SLIDES.length; idx += 1) {
    const data = SLIDES[idx - 1];
    if (data.layout === "cover") {
      await slideCover(presentation);
    } else if (data.layout === "promptlist") {
      await slidePromptList(presentation, idx);
    } else if (data.layout === "flow") {
      await slideFlow(presentation, idx);
    } else if (data.layout === "frontend") {
      await slideFrontend(presentation, idx);
    } else if (data.layout === "proof") {
      await slideProof(presentation, idx);
    } else if (data.layout === "references") {
      await slideReferences(presentation, idx);
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
    inspectRecords.push({ kind: "slide", slide: index + 1, id: slide?.id || `slide-${index + 1}` });
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
  await writeInspectArtifact(presentation);
  const loop = await nextRenderLoopNumber();
  if (loop > 3) throw new Error("Render loop cap reached");

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
  await appendRenderVerifyLoop(presentation, previewPaths, pptxPath);
  return pptxPath;
}

const presentation = await createDeck();
const pptxPath = await verifyAndExport(presentation);
console.log(pptxPath);
