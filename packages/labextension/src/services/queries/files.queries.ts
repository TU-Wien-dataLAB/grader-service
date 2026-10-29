import { queryOptions } from '@tanstack/react-query';
import { loadString } from '../storage.service';

export const selectedDirQuery = (lectureId: number, assignmentId: number) =>
  queryOptions({
    queryKey: ['selectedDir', lectureId, assignmentId],
    queryFn: async () => {
      const data = loadString(
        `${lectureId}:${assignmentId}:files-selected-dir`
      );
      // default to 'source' if no value is stored
      return data || 'source';
    }
  });
