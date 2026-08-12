import { GlobalObjects } from '../index';

export const goToPath = async (path: string) => {
  await GlobalObjects.commands.execute('filebrowser:go-to-path', {
    path: path
  });
};
