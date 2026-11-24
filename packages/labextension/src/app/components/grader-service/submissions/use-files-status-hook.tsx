import { useCallback, useEffect, useMemo, useState } from 'react';
import { Contents } from '@jupyterlab/services';
import {
  isFileChanged,
  resetFileBaseline,
  clearFileBaseline,
  fileStatusKey,
  FILE_STATUS_EVENT,
  ensureFileBaseline
} from '../../../../services/file-status.service';
import { GlobalObjects } from '../../../../index';

// Core hook: tracks changed state for many files
export function useFilesChanged(paths: string[]) {
  const [changedMap, setChangedMap] = useState<Record<string, boolean>>({});
  const pathsKey = paths.join('\n');

  useEffect(() => {
    const pathSet = new Set(paths);
    // Drop entries for paths that no longer exist
    setChangedMap(prev => {
      const next: Record<string, boolean> = {};
      for (const path of paths) if (path in prev) next[path] = prev[path];
      return next;
    });

    if (paths.length === 0) return;

    let active = true;
    const keyPrefix = fileStatusKey('');

    const checkFile = async (path: string) => {
      let res = false;
      try {
        res = await isFileChanged(path);
      } catch {
        res = false;
      }
      if (!active) return;
      setChangedMap(prev =>
        prev[path] === res ? prev : { ...prev, [path]: res }
      );
    };

    const checkAllFiles = () => paths.forEach(checkFile);

    const onFileChanged = (
      _: Contents.IManager,
      args: Contents.IChangedArgs
    ) => {
      const path = args.newValue?.path;
      if (args.type === 'save' && path && pathSet.has(path)) checkFile(path);
    };

    const onBaselineChanged = (e: Event) => {
      const path = (e as CustomEvent).detail?.filePath;
      if (path && pathSet.has(path)) checkFile(path);
    };

    const onStorage = (e: StorageEvent) => {
      if (e.key === null) checkAllFiles();
      else if (e.key.startsWith(keyPrefix)) {
        const path = e.key.slice(keyPrefix.length);
        if (pathSet.has(path)) checkFile(path);
      }
    };

    GlobalObjects.serviceManager.contents.fileChanged.connect(onFileChanged);
    window.addEventListener(FILE_STATUS_EVENT, onBaselineChanged);
    window.addEventListener('storage', onStorage);

    Promise.all(paths.map(path => ensureFileBaseline(path)))
      .then(checkAllFiles)
      .catch(() => {
        if (active) checkAllFiles();
      });

    return () => {
      active = false;
      GlobalObjects.serviceManager.contents.fileChanged.disconnect(
        onFileChanged
      );
      window.removeEventListener(FILE_STATUS_EVENT, onBaselineChanged);
      window.removeEventListener('storage', onStorage);
    };
  }, [pathsKey]);

  const anyChanged = useMemo(
    () => Object.values(changedMap).some(Boolean),
    [changedMap]
  );

  const resetBaselines = useCallback(
    () => Promise.all(paths.map(path => resetFileBaseline(path))),
    [pathsKey]
  );

  const clearBaselines = useCallback(() => {
    paths.forEach(path => clearFileBaseline(path));
  }, [pathsKey]);

  return { changedMap, anyChanged, resetBaselines, clearBaselines };
}

// Single-file change tracker, read-only
export function useFileStatus(filePath?: string) {
  const paths = useMemo(() => (filePath ? [filePath] : []), [filePath]);
  const { changedMap, resetBaselines, clearBaselines } = useFilesChanged(paths);

  const changed = filePath ? (changedMap[filePath] ?? null) : null;

  return {
    changed,
    resetBaseline: resetBaselines,
    clearFileBaseline: clearBaselines
  };
}
