// Turn the single-file Vite build into a hosted-page body: the host adds the document
// skeleton, so keep only <title>, font links, styles, the root element and scripts.
import { readFileSync, writeFileSync } from "node:fs";

const html = readFileSync("dist-artifact/index.html", "utf8");
const head = html.match(/<head>([\s\S]*?)<\/head>/i)[1];
const title = head.match(/<title>[\s\S]*?<\/title>/i)[0];
const links = [...head.matchAll(/<link[^>]+fonts\.(googleapis|gstatic)[^>]*>/gi)].map((m) => m[0]).join("\n");
const styles = [...html.matchAll(/<style[^>]*>[\s\S]*?<\/style>/gi)].map((m) => m[0]).join("\n");
const scripts = [...html.matchAll(/<script[^>]*>[\s\S]*?<\/script>/gi)].map((m) => m[0]).join("\n");
const page = `${title}\n${links}\n${styles}\n<div id="root"></div>\n${scripts}\n`;
writeFileSync("dist-artifact/page.html", page);
console.log(`page.html ${(page.length / 1024).toFixed(0)} KB`);
