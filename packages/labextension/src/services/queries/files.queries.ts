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

export const assignmentFilesStatusQuery = (
lectureId: number,
assignmentId: number,
lectureCode?: string
) =>
queryOptions({
  queryKey: ['filesStatus', lectureId, assignmentId],
  queryFn: async () => {
    const files = await getFiles(
      `${lectureBasePath}${lectureCode}/assignments/${assignmentId}`
    );
    return (files?.length ?? 0) > 0;
  },
  enabled: !!lectureCode
});