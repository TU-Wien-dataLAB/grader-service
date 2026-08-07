import { GlobalObjects } from '../index';
import { PageConfig } from '@jupyterlab/coreutils';

const raw = PageConfig.getOption('lectures_base_path').replace(
  /^\/+|\/+$/g,
  ''
);
export const lectureBasePath = raw && `${raw}/`;

export const lectureSubPaths = (lectureBasePath as string)
  .split('/')
  .reduce((acc, v) => (v.length > 0 ? acc + 1 : acc), 0);

export const openFile = async (path: string) => {
  await GlobalObjects.commands.execute('docmanager:open', {
    path: path,
    options: {
      mode: 'tab-after' // tab-after tab-before split-bottom split-right split-left split-top
    }
  });
};
