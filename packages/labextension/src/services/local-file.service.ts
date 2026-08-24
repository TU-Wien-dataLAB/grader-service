/**
 * Local File Service - a class that manipulates the local file system in JupyterLab
 */
import { GlobalObjects } from '../index';
import { PageConfig, PathExt } from '@jupyterlab/coreutils';
import { FileBrowserModel } from '@jupyterlab/filebrowser';

// extract lecture base path from jupyterlab's app config (set in grader_labextension/handlers/base_handler.py)
const raw = PageConfig.getOption('lectures_base_path').replace(
  /^\/+|\/+$/g,
  ''
);

// append / so that lectureBasePath can be prepended to any string as a valid path
export const lectureBasePath = raw && `${raw}/`;

// the number of sub paths in lecture base path e.g. grader/Lectures -> 2
export const lectureSubPathsCount = (lectureBasePath as string)
  .split('/')
  .reduce((acc, v) => (v.length > 0 ? acc + 1 : acc), 0);

// builds the base path for a given assignment in the file browser, e.g. lectures/lec1/assignments/1/
const buildFileBasePath = (
  lectureCode: string,
  type: string,
  assignmentId: number
) => {
  return `${lectureBasePath}${lectureCode}/${type}/${assignmentId}/`;
};
/**
 * Route to the given path in the file browser (Jupyterlab's sidebar)
 *
 * @param path path to route to
 */
export const openInFileBrowser = async (path: string) => {
  await GlobalObjects.commands.execute('filebrowser:go-to-path', {
    path: path
  });
};

/**
 * Opens a file in a new tab
 *
 * @param path file path to open
 * @param mode determines how to open a file. Default: tab-after
 */
export const openInNewTab = async (
  path: string,
  mode: string = 'tab-after'
) => {
  await GlobalObjects.commands.execute('docmanager:open', {
    path: path,
    options: {
      mode: mode // tab-after tab-before split-bottom split-right split-left split-top
    }
  });
};

export interface IFile {
  name: string;
  path: string;
  type: string;
  content: IFile[];
}

/**
 * Get all files in a given path (for displaying in the UI)
 *
 * @param path path to get files from
 */
export const getFiles = async (path: string): Promise<IFile[]> => {
  if (path === null) {
    return [];
  }

  const model = new FileBrowserModel({
    auto: false,
    manager: GlobalObjects.docManager,
    refreshInterval: 1000000
  });

  try {
    await model.cd(path);
    await model.refresh();
  } catch (_) {
    return [];
  }

  if (model.path !== path) {
    return [];
  }

  const items = model.items();
  const files: IFile[] = [];

  let f = items.next();
  while (f.value !== undefined) {
    if (f.value.type === 'directory') {
      const nestedFiles = await getFiles(f.value.path);
      files.push({
        name: f.value.name,
        path: f.value.path,
        type: f.value.type,
        content: nestedFiles
      });
    } else {
      files.push({
        name: f.value.name,
        path: f.value.path,
        type: f.value.type,
        content: []
      });
    }
    f = items.next();
  }
  return files;
};

export const getRelativePath = (
  lectureCode: string,
  type: 'assignments' | 'source' | 'release',
  assignmentId: number,
  path: string
) => {
  return PathExt.relative(
    buildFileBasePath(lectureCode, type, assignmentId),
    path
  );
};

export const extractRelativePaths = (
  lectureCode: string,
  type: 'assignments' | 'source' | 'release',
  assignmentId: number,
  file: IFile
) => {
  if (file.type === 'directory') {
    const nestedPaths: any[] = file.content.flatMap(nestedFile =>
      extractRelativePaths(lectureCode, type, assignmentId, nestedFile)
    );
    return [
      getRelativePath(lectureCode, type, assignmentId, file.path),
      ...nestedPaths
    ];
  } else {
    return [getRelativePath(lectureCode, type, assignmentId, file.path)];
  }
};

const makeDir = async (path: string, name: string) => {
  const newPath = PathExt.join(path, name);
  let exists = false;
  const model = new FileBrowserModel({
    auto: false,
    manager: GlobalObjects.docManager,
    refreshInterval: 1000000
  });
  try {
    await model.cd(path);
    await model.refresh();
  } catch (_) {
    exists = false;
  }
  const items = model.items();
  let f = items.next();
  while (f.value !== undefined) {
    if (f.value.type === 'directory') {
      if (f.value.name === name) {
        exists = true;
      }
    }
    f = items.next();
  }

  if (!exists) {
    const model = await GlobalObjects.docManager.newUntitled({
      path,
      type: 'directory'
    });
    const oldPath = PathExt.join(path, model.name);
    await GlobalObjects.docManager.rename(oldPath, newPath).catch(error => {
      if (error.response.status !== 409) {
        // if it's not caused by an already existing file, rethrow
        throw error;
      }
    });
  }
  return newPath;
};

/**
 * Make a directory at the given path
 */
export const makeDirs = async (path: string, names: string[]) => {
  let p = path;
  names.map(async name => {
    p = await makeDir(p, name);
  });
  return p;
};
