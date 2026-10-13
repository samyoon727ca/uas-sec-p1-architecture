// Render overview/build/overview.md (written by tools/gen_overview.py) to
// overview/overview.pdf with Chrome, through puppeteer.
//
// Headings: "# Title {#id}" sets the anchor; "{-}" leaves a heading unnumbered.
// Level-1 headings are chapters and start a new page; levels 1 and 2 are
// numbered and listed in the contents, which replaces "<!-- toc -->".
// "<!-- toolchain -->" is replaced by the versions that built this PDF.
//
// Page numbers in the contents: Chrome cannot compute them (no CSS
// target-counter), so the PDF is printed once with placeholder numbers, the
// page of each heading is read from the PDF's named destinations, and it is
// printed again with the real numbers until no heading moves.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import MarkdownIt from "markdown-it";
import puppeteer from "puppeteer";

const here = path.dirname(fileURLToPath(import.meta.url));
const build = path.join(here, "build");
const source = fs.readFileSync(path.join(build, "overview.md"), "utf8");
const provenance = JSON.parse(fs.readFileSync(path.join(build, "provenance.json"), "utf8"));
const css = fs.readFileSync(path.join(here, "style.css"), "utf8");

const md = new MarkdownIt({ html: true, linkify: false, typographer: false });
const toc = [];
const ids = new Set();
const heads = new Map();

// Heading ids, numbers and the contents list.
md.core.ruler.push("overview_headings", (state) => {
  const counters = [0, 0];
  const tokens = state.tokens;
  for (let i = 0; i < tokens.length; i++) {
    if (tokens[i].type !== "heading_open") continue;
    const level = Number(tokens[i].tag.slice(1));
    const inline = tokens[i + 1];
    let text = inline.content;
    let id = null;
    let numbered = level <= 2;
    const attrs = text.match(/\s*\{([^}]*)\}\s*$/);
    if (attrs) {
      text = text.slice(0, attrs.index);
      for (const a of attrs[1].split(/\s+/)) {
        if (a.startsWith("#")) id = a.slice(1);
        else if (a === "-") numbered = false;
      }
      const last = inline.children[inline.children.length - 1];
      last.content = last.content.replace(/\s*\{[^}]*\}\s*$/, "");
    }
    if (!id) id = text.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
    let base = id;
    for (let n = 2; ids.has(id); n++) id = `${base}-${n}`;
    ids.add(id);
    tokens[i].attrSet("id", id);
    let number = "";
    if (numbered && level === 1) {
      counters[0] += 1;
      counters[1] = 0;
      number = `${counters[0]}`;
    } else if (numbered && level === 2 && counters[0] > 0) {
      counters[1] += 1;
      number = `${counters[0]}.${counters[1]}`;
    }
    if (number) {
      const num = new state.Token("html_inline", "", 0);
      num.content = `<span class="num">${number}</span> `;
      inline.children.unshift(num);
    }
    if (level === 1) tokens[i].attrJoin("class", "chapter");
    // The numbered section an unnumbered heading sits in, for cross-references.
    const within = level > 2 && counters[0] ? (counters[1] ? `§${counters[0]}.${counters[1]}` : `chapter ${counters[0]}`) : "";
    const entry = { level, id, number, within, text: md.renderInline(text) };
    heads.set(id, entry);
    if (level <= 2 && (numbered || level === 1)) toc.push(entry);
  }
});

// External links open the URL; the printed text shows where they go.
md.renderer.rules.link_open = (tokens, idx, options, env, self) => {
  const href = tokens[idx].attrGet("href") || "";
  if (/^https?:/.test(href)) tokens[idx].attrJoin("class", "ext");
  return self.renderToken(tokens, idx, options);
};

// "[](#id)" becomes a cross-reference: "chapter N" for a chapter, "§N.M" for a
// numbered section, and for an unnumbered heading its text and the numbered
// section it sits in ("“Title” in §N.M"). An unknown id fails the build.
const body = md.render(source).replace(/<a href="#([^"]+)"><\/a>/g, (_, id) => {
  const t = heads.get(id);
  if (!t) throw new Error(`cross-reference to unknown id #${id}`);
  const label = t.number
    ? t.level === 1 ? `chapter ${t.number}` : `§${t.number}`
    : t.within ? `“${t.text}” in ${t.within}` : t.text;
  return `<a href="#${id}">${label}</a>`;
});
// A short identifier in a table's first column (SR-005, TC-04e-control) must not
// break at its hyphens.
const tagged = body.replace(/<tr>\n<td>((?:[^<\s]{1,22}|<code>[^<\s]{1,26}<\/code>))<\/td>/g, '<tr>\n<td class="id">$1</td>');
const tocEntries = toc.filter((t) => t.id !== "contents");
const tocHtml = (pages) =>
  '<nav class="toc"><ol>' +
  tocEntries
    .map(
      (t) =>
        `<li class="l${t.level}"><a href="#${t.id}"><span class="num">${t.number}</span>` +
        `<span class="text">${t.text}</span><span class="leader"></span>` +
        `<span class="page">${pages ? pages.get(t.id) : "00"}</span></a></li>`,
    )
    .join("") +
  "</ol></nav>";

function pkgVersion(name) {
  return JSON.parse(fs.readFileSync(path.join(here, "node_modules", name, "package.json"), "utf8")).version;
}

// The page number of every named destination in a PDF printed by Chrome
// (Skia writes the catalog, page tree and /Dests dictionary uncompressed).
// Fails loudly if the structure is not found, rather than guessing.
function destinationPages(bytes) {
  const s = Buffer.from(bytes).toString("latin1");
  const object = (n) => {
    const start = s.indexOf(`\n${n} 0 obj\n`);
    if (start < 0) throw new Error(`PDF object ${n} not found`);
    return s.slice(start, s.indexOf("\nendobj", start));
  };
  const catalog = s.match(/\n\d+ 0 obj\n<<\/Type \/Catalog[\s\S]*?\nendobj/);
  const pagesRef = catalog && catalog[0].match(/\/Pages (\d+) 0 R/);
  const destsRef = catalog && catalog[0].match(/\/Dests (\d+) 0 R/);
  if (!pagesRef || !destsRef) throw new Error("PDF catalog with /Pages and /Dests not found");
  const order = [];
  const walk = (n) => {
    const o = object(n);
    if (/\/Type \/Pages[\s/>]/.test(o)) {
      for (const kid of o.match(/\/Kids \[([^\]]*)\]/)[1].match(/\d+ 0 R/g)) walk(parseInt(kid, 10));
    } else {
      order.push(n);
    }
  };
  walk(parseInt(pagesRef[1], 10));
  const pageOf = new Map(order.map((n, i) => [n, i + 1]));
  const dests = new Map();
  for (const m of object(destsRef[1]).matchAll(/\/([^\s[\]/<>()]+) \[(\d+) 0 R /g)) {
    const name = m[1].replace(/#([0-9a-fA-F]{2})/g, (_, h) => String.fromCharCode(parseInt(h, 16)));
    dests.set(name, pageOf.get(parseInt(m[2], 10)));
  }
  return { dests, pages: order.length };
}

const browser = await puppeteer.launch({
  executablePath: process.env.CHROME_PATH,
  args: ["--no-sandbox", "--font-render-hinting=none"],
});
try {
  const chrome = await browser.version();
  const toolchain =
    `Node.js ${process.version}; ${chrome}; markdown-it ${pkgVersion("markdown-it")}; ` +
    `@mermaid-js/mermaid-cli ${pkgVersion("@mermaid-js/mermaid-cli")} with mermaid ${pkgVersion("mermaid")}; ` +
    `puppeteer ${pkgVersion("puppeteer")}`;
  const htmlPath = path.join(build, "overview.html");
  const p1 = provenance.p1_head.slice(0, 7) + (provenance.p1_dirty ? "+changes" : "");
  const footer = `<div style="width:100%; font-size:7.5pt; color:#555; padding:0 0.8in; display:flex;
      justify-content:space-between; font-family:'DejaVu Sans','Liberation Sans',sans-serif;">
    <span>UAS security portfolio overview · P1 ${p1} (data ${provenance.p1_data.slice(0, 7)}) · P2 ${provenance.p2.slice(0, 7)}</span>
    <span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>`;
  const page = await browser.newPage();

  async function print(pages) {
    const html = `<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>UAS security portfolio: overview</title>
<style>${css}</style></head>
<body>${tagged.replace("<!-- toc -->", tocHtml(pages)).replace("<!-- toolchain -->", toolchain)}</body></html>`;
    fs.writeFileSync(htmlPath, html);
    await page.goto(pathToFileURL(htmlPath).href, { waitUntil: "load" });
    await page.evaluate(() => document.fonts.ready);
    const broken = await page.evaluate(() =>
      [...document.images].filter((img) => !img.complete || img.naturalWidth === 0).map((img) => img.src),
    );
    if (broken.length) throw new Error(`images that did not load: ${broken.join(", ")}`);
    return page.pdf({
      format: "Letter",
      printBackground: true,
      displayHeaderFooter: true,
      headerTemplate: "<div></div>",
      footerTemplate: footer,
      margin: { top: "0.7in", bottom: "0.75in", left: "0.8in", right: "0.8in" },
      outline: true,
      tagged: true,
    });
  }

  let pages = null;
  for (let pass = 1; ; pass++) {
    const pdf = await print(pages);
    const found = destinationPages(pdf);
    const missing = tocEntries.filter((t) => !found.dests.get(t.id)).map((t) => t.id);
    if (missing.length) throw new Error(`no page found for contents entries: ${missing.join(", ")}`);
    if (pages && tocEntries.every((t) => pages.get(t.id) === found.dests.get(t.id))) {
      fs.writeFileSync(path.join(here, "overview.pdf"), pdf);
      console.log(`overview.pdf written: ${found.pages} pages (${pass} passes); ${toolchain}`);
      break;
    }
    if (pass === 4) throw new Error("contents page numbers did not settle after 4 passes");
    pages = found.dests;
  }
} finally {
  await browser.close();
}
