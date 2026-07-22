import { readFileSync } from 'node:fs';
import { parse } from 'yaml';

// Parse a `---`-delimited YAML frontmatter block from a markdown file.
// Returns { data, body, raw } — data is null when there is no frontmatter,
// and an Error instance in `error` when the block exists but does not parse.
export function readFrontmatter(path) {
  const text = readFileSync(path, 'utf8');
  if (!text.startsWith('---\n') && !text.startsWith('---\r\n')) {
    return { data: null, body: text, error: null };
  }
  const end = text.indexOf('\n---', 3);
  if (end === -1) {
    return { data: null, body: text, error: new Error('unterminated frontmatter block') };
  }
  const raw = text.slice(text.indexOf('\n') + 1, end);
  const body = text.slice(text.indexOf('\n', end + 1) + 1);
  try {
    const data = parse(raw);
    if (data !== null && typeof data !== 'object') {
      return { data: null, body, error: new Error('frontmatter is not a YAML mapping') };
    }
    return { data: data ?? {}, body, error: null };
  } catch (e) {
    return { data: null, body, error: e };
  }
}

// Strip fenced code blocks so link/pattern scans don't trip on examples.
export function stripCodeFences(markdown) {
  return markdown.replace(/^(```|~~~).*?^\1[^\S\n]*$/gms, '');
}
