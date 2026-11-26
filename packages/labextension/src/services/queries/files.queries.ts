import { queryOptions } from '@tanstack/react-query';
import { loadString } from '../storage.service';
import { getFiles, lectureBasePath } from '../local-file.service';

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

export const filesQuery = (
  lectureCode: string,
  assignmentId: number,
  dir: string,
  enabled = true
) =>
  queryOptions({
    queryKey: ['files', lectureCode, dir, assignmentId],
    queryFn: async () =>
      await getFiles(`${lectureBasePath}${lectureCode}/${dir}/${assignmentId}`),
    enabled: enabled
  });
