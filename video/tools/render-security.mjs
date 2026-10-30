import fs from 'node:fs';
import path from 'node:path';

export function validateName(name, maxLength = 120) {
  // Portable filename only: reject traversal, NTFS streams, control characters and device names.
  if (typeof name !== 'string' || !name || name.length > maxLength ||
      /[<>:"/\\|?*\x00-\x1f\x7f]/u.test(name) || /[. ]$/u.test(name) ||
      /^(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)/iu.test(name)) {
    throw new Error('--name must be a filename, without path separators or reserved characters');
  }
  return name;
}

export function readData(file) {
  if (!file) return undefined;
  const data = JSON.parse(fs.readFileSync(file, 'utf8'));
  if (data === null || typeof data !== 'object' || Array.isArray(data)) {
    throw new Error('--data must contain a JSON object');
  }
  return data;
}

export async function injectData(page, data) {
  if (data !== undefined) await page.addInitScript(value => { window.RETRO_DATA = value; }, data);
}

export function outputFile(outDir, filename) {
  validateName(filename, 240);
  const target = path.resolve(outDir, filename);
  if (path.dirname(target) !== path.resolve(outDir)) throw new Error('Output escapes --out');
  // Do not follow a pre-existing symlink when ffmpeg or Playwright opens an output.
  try {
    if (!fs.lstatSync(target).isFile()) throw new Error(`Output is not a regular file: ${target}`);
  } catch (e) {
    if (e.code !== 'ENOENT') throw e;
  }
  return target;
}

export function createWorkspace(outDir) {
  // The parent is resolved once; cleanup can only remove this newly allocated child.
  const parent = fs.realpathSync(outDir);
  const dir = fs.mkdtempSync(path.join(parent, '.retro-render-'));
  return {
    dir,
    cleanup() {
      if (path.dirname(dir) !== parent) throw new Error('Refusing unsafe cleanup');
      fs.rmSync(dir, { recursive: true, force: true });
    },
  };
}
