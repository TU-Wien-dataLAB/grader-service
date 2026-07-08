// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import { FileBrowserModel } from '@jupyterlab/filebrowser/lib/model';
import { GlobalObjects } from '../index';
import { Assignment } from '../model/assignment';
import { HTTPMethod, request } from './request.service';
import { Lecture } from '../model/lecture';
import { RepoType } from '../components/util/repo-type';
import { PageConfig, PathExt } from '@jupyterlab/coreutils';
import { enqueueSnackbar } from 'notistack';
import { RemoteFileStatus } from '../model/remoteFileStatus';

// remove slashes at beginning and end of base path if they exist
export let lectureBasePath = PageConfig.getOption('lectures_base_path').replace(
  /^\/|\/$/g,
  ''
);

// append / so that lectureBasePath can be prepended to any string and becomes a valid path
if (lectureBasePath !== '') {
  lectureBasePath += '/';
}

// the number of sub paths in lecture base path e.g. grader/Lectures -> 2
export const lectureSubPaths: number = lectureBasePath
  .split('/')
  .reduce((acc, v) => (v.length > 0 ? acc + 1 : acc), 0);

export interface File {
  name: string;
  path: string;
  type: string;
  content: File[];
}

export const getFiles = async (path: string): Promise<File[]> => {
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
  const files: File[] = []; // Type files as File[]

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
  path: string,
  reg: 'assignments' | 'source'
) => {
  const regexStr = `${reg}\/[^/]+\/(.+)`;
  const regex = new RegExp(regexStr);
  const match = path.match(regex);
  return match ? match[1] : path;
};

export const extractRelativePaths = (
  file: File,
  reg: 'assignments' | 'source'
) => {
  if (file.type === 'directory') {
    const nestedPaths = file.content.flatMap(nestedFile =>
      extractRelativePaths(nestedFile, reg)
    );
    return [getRelativePath(file.path, reg), ...nestedPaths];
  } else {
    return [getRelativePath(file.path, reg)];
  }
};

export const openFile = async (path: string) => {
  GlobalObjects.commands
    .execute('docmanager:open', {
      path: path,
      options: {
        mode: 'tab-after' // tab-after tab-before split-bottom split-right split-left split-top
      }
    })
    .catch(error => {
      enqueueSnackbar(error.message, {
        variant: 'error'
      });
    });
};

export const makeDir = async (path: string, name: string) => {
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

  console.log('directory: ' + name + ' exists: ' + exists);
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
  console.log('new path created: ' + newPath);
  return newPath;
};

// makeDirs creates multiple directories in a given path
export const makeDirs = async (path: string, names: string[]) => {
  let p = path;
  for (let i = 0; i < names.length; i++) {
    const n = names[i];
    p = await makeDir(p, n);
  }
  return p;
};

export interface IGitLogObject {
  commit: string;
  author: string;
  date: string;
  ref: string;
  commit_msg: string;
  pre_commit: string;
}

export function getGitLog(
  lecture: Lecture,
  assignment: Assignment,
  repo: RepoType,
  nCommits: number
): Promise<IGitLogObject[]> {
  let url = `/api/lectures/${lecture.id}/assignments/${assignment.id}/log/${repo}/`;
  const searchParams = new URLSearchParams({
    n: String(nCommits)
  });
  url += '?' + searchParams;
  return request<IGitLogObject[]>(HTTPMethod.GET, url, null, true);
}

export function getRemoteStatus(
  lecture: Lecture,
  assignment: Assignment,
  repo: RepoType,
  reload = false
): Promise<RemoteFileStatus> {
  const url = `/api/lectures/${lecture.id}/assignments/${assignment.id}/remote-status/${repo}/`;
  return request<RemoteFileStatus>(HTTPMethod.GET, url, null, reload);
}

export function getRemoteFileStatus(
  lecture: Lecture,
  assignment: Assignment,
  repo: RepoType,
  filePath: string,
  reload = false
): Promise<RemoteFileStatus> {
  const url = `/api/lectures/${lecture.id}/assignments/${
    assignment.id
  }/remote-file-status/${repo}/?file=${encodeURIComponent(filePath)}`;
  return request<RemoteFileStatus>(HTTPMethod.GET, url, null, reload);
}
