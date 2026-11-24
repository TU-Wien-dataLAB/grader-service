import { GlobalObjects } from '../index';

const STORAGE_PREFIX = 'grader-file-hash:';
export const FILE_STATUS_EVENT = 'localStorageUpdate';

export const fileStatusKey = (filePath: string) => STORAGE_PREFIX + filePath;

const notify = (filePath: string) =>
  window.dispatchEvent(
    new CustomEvent(FILE_STATUS_EVENT, { detail: { filePath } })
  );

async function getFileHash(filePath: string): Promise<string> {
  const model = await GlobalObjects.serviceManager.contents.get(filePath, {
    content: true
  });
  const text =
    typeof model.content === 'string'
      ? model.content
      : JSON.stringify(model.content);

  const buf = await crypto.subtle.digest(
    'SHA-256',
    new TextEncoder().encode(text)
  );
  return Array.from(new Uint8Array(buf))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');
}

/**
 * Pure read: never writes to storage and never dispatches events.
 * Returns false when no baseline exists yet.
 */
export async function isFileChanged(filePath: string): Promise<boolean> {
  const baseline = localStorage.getItem(fileStatusKey(filePath));
  if (baseline === null) return false;
  return (await getFileHash(filePath)) !== baseline;
}

/**
 * Records a baseline only if none exists. Notifies only if it actually wrote.
 */
export async function ensureFileBaseline(filePath: string): Promise<void> {
  const key = fileStatusKey(filePath);
  if (localStorage.getItem(key) !== null) return;
  localStorage.setItem(key, await getFileHash(filePath));
  notify(filePath);
}

/**
 * Re-baselines to the file's current content.
 * Call this AFTER a pull/reset has finished writing the file.
 */
export async function resetFileBaseline(filePath: string): Promise<void> {
  const key = fileStatusKey(filePath);
  const hash = await getFileHash(filePath);
  if (localStorage.getItem(key) === hash) return;
  localStorage.setItem(key, hash);
  notify(filePath);
}

/**
 * Removes the baseline entirely.
 */
export function clearFileBaseline(filePath: string): void {
  localStorage.removeItem(fileStatusKey(filePath));
  notify(filePath);
}
