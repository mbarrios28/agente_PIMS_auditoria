// Uso: node scripts/render_arquitectura.mjs [ruta/al/paquete/@viz-js/viz/dist/viz.js]
import { readFile, writeFile } from 'node:fs/promises';
import { pathToFileURL, fileURLToPath } from 'node:url';
const module = process.argv[2] ? await import(pathToFileURL(process.argv[2])) : await import('@viz-js/viz');
const viz = await module.instance();
const base = new URL('../docs/entrega_ec2/assets/', import.meta.url);
const dot = await readFile(new URL('arquitectura.dot', base), 'utf8');
const svg = viz.renderString(dot, { format: 'svg', engine: 'dot' });
await writeFile(new URL('arquitectura.svg', base), svg);
console.log(`Graphviz: ${fileURLToPath(new URL('arquitectura.svg', base))}`);
