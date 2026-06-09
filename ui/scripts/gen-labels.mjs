// Generate ui/src/lib/labels.generated.json from the canonical label registry
// data/ref/labels.csv (the single source of truth, M2/M3). Run via `npm run
// gen:labels` (also wired to `prebuild`). The generated JSON is committed so the
// build works even where data/ isn't present.
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const CSV = resolve(here, "../../data/ref/labels.csv");
const OUT = resolve(here, "../src/lib/labels.generated.json");

// Minimal RFC-4180-ish CSV parser (handles quoted fields with commas/newlines
// and "" escapes; Czech „…" quotes are not ASCII " so they don't interfere).
function parseCSV(text) {
  const rows = [];
  let row = [], field = "", inQ = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (inQ) {
      if (c === '"') {
        if (text[i + 1] === '"') { field += '"'; i++; } else inQ = false;
      } else field += c;
    } else if (c === '"') inQ = true;
    else if (c === ",") { row.push(field); field = ""; }
    else if (c === "\n") { row.push(field); rows.push(row); row = []; field = ""; }
    else if (c !== "\r") field += c;
  }
  if (field.length || row.length) { row.push(field); rows.push(row); }
  return rows;
}

const rows = parseCSV(readFileSync(CSV, "utf8")).filter((r) => r.length > 1 && r[0]);
const header = rows[0];
const out = {};
for (const r of rows.slice(1)) {
  const obj = {};
  header.forEach((h, i) => (obj[h] = (r[i] ?? "").trim()));
  out[obj.id] = obj;
}
mkdirSync(dirname(OUT), { recursive: true });
writeFileSync(OUT, JSON.stringify(out, null, 2) + "\n", "utf8");
console.log(`[gen-labels] wrote ${Object.keys(out).length} concepts -> ${OUT}`);
