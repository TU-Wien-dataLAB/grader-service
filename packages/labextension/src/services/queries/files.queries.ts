import { queryOptions } from '@tanstack/react-query';
import { loadString } from '../storage.service';

export const selectedDirQuery = () =>
  queryOptions({
    queryKey: ['selectedDir'],
    queryFn: async () => {
      const data = loadString('files-selected-dir');
      // default to 'source' if no value is stored
      return data || 'source';
    }
  });
