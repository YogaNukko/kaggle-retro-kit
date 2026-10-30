import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import { createWorkspace, injectData, outputFile, readData, validateName } from '../tools/render-security.mjs';

const renderer = fileURLToPath(new URL('../tools/render.mjs', import.meta.url));
const example = fileURLToPath(new URL('../pages/custom-example.html', import.meta.url));
function fixture(t) {
  const parent = fs.realpathSync(os.tmpdir());
  const dir = fs.mkdtempSync(path.join(parent, 'retro-security-'));
  t.after(() => {
    assert.equal(path.dirname(dir), parent);
    fs.rmSync(dir, { recursive: true, force: true });
  });
  return dir;
}

test('reject traversal and reserved names before creating output or loading a browser', t => {
  const root = fixture(t);
  const out = path.join(root, 'out');
  for (const name of ['.', '..', '../outside', '..\\outside', '/tmp/escape', 'C:\\escape', 'file:stream', 'NUL', 'CON.txt', 'bad\nname', 'trailing.']) {
    assert.throws(() => validateName(name));
    const result = spawnSync(process.execPath, [renderer, 'video', '--page', example, '--out', out, '--name', name], { encoding: 'utf8' });
    assert.equal(result.status, 1);
    assert.match(result.stderr, /--name/);
    assert.equal(fs.existsSync(out), false);
  }
  assert.equal(validateName('大会-2026.scene'), '大会-2026.scene');
});

test('invalid JSON cannot execute and is rejected before creating output', t => {
  const root = fixture(t);
  const data = path.join(root, 'data.json');
  const out = path.join(root, 'out');
  fs.writeFileSync(data, '{}; window.injected = true; //');
  assert.throws(() => readData(data), SyntaxError);
  const result = spawnSync(process.execPath, [renderer, 'info', '--page', example, '--data', data, '--out', out], { encoding: 'utf8' });
  assert.equal(result.status, 1);
  assert.equal(fs.existsSync(out), false);
  for (const text of ['null', '[]', '42', '"text"']) {
    fs.writeFileSync(data, text);
    assert.throws(() => readData(data), /JSON object/);
  }
});

test('JSON values are passed separately from script source', async t => {
  const root = fixture(t);
  const file = path.join(root, 'data.json');
  const data = { text: '"; window.injected = true; // </script>', name: '日本語' };
  fs.writeFileSync(file, JSON.stringify(data));
  let called = false;
  await injectData({ addInitScript: async (fn, value) => {
    called = true;
    assert.equal(typeof fn, 'function');
    assert.deepEqual(value, data);
    assert.equal(fn.toString().includes('window.injected'), false);
  } }, readData(file));
  assert.equal(called, true);
});

test('cleanup preserves pre-existing frame and sheet directories and concurrent workspaces', t => {
  const root = fixture(t);
  for (const name of ['frames', '_sheet']) {
    fs.mkdirSync(path.join(root, name));
    fs.writeFileSync(path.join(root, name, 'keep.txt'), 'keep');
  }
  const first = createWorkspace(root), second = createWorkspace(root);
  assert.notEqual(first.dir, second.dir);
  fs.writeFileSync(path.join(first.dir, 'frame.png'), 'temporary');
  first.cleanup();
  assert.equal(fs.existsSync(first.dir), false);
  assert.equal(fs.existsSync(second.dir), true);
  for (const name of ['frames', '_sheet']) assert.equal(fs.readFileSync(path.join(root, name, 'keep.txt'), 'utf8'), 'keep');
  second.cleanup();
});

test('output paths reject traversal and symbolic links', t => {
  const root = fixture(t);
  assert.throws(() => outputFile(root, '../escape.mp4'));
  const target = path.join(root, 'target');
  fs.mkdirSync(target);
  const link = path.join(root, 'linked.mp4');
  fs.symlinkSync(target, link, process.platform === 'win32' ? 'junction' : 'dir');
  assert.throws(() => outputFile(root, 'linked.mp4'), /regular file/);
  assert.equal(outputFile(root, 'safe.mp4'), path.join(root, 'safe.mp4'));
});

test('real sandboxed Chromium receives hostile strings as data', { skip: !process.env.RETRO_BROWSER_TESTS }, async () => {
  const { chromium } = await import('playwright-core');
  const browser = await chromium.launch({ chromiumSandbox: true });
  try {
    const page = await browser.newPage();
    const data = { text: '"; window.injected = true; // </script>' };
    await injectData(page, data);
    await page.goto('data:text/html,<html></html>');
    assert.deepEqual(await page.evaluate(() => window.RETRO_DATA), data);
    assert.equal(await page.evaluate(() => window.injected), undefined);
  } finally { await browser.close(); }
});
