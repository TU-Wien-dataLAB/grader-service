import { GlobalObjects } from '../index';
import { enqueueSnackbar } from 'notistack';

export const goToPath = async (path: string) => {
  GlobalObjects.commands
    .execute('filebrowser:go-to-path', {
      path: path
    })
    .catch(error => {
      enqueueSnackbar(error.message, { variant: 'error' });
    });
};
