import { queryOptions } from '@tanstack/react-query';
import { getLecture } from '../lectures.service';
import { getFiles } from '../local-file.service';

export const Query = (lectureId: number) =>
  queryOptions({
    queryKey: ['lectures', lectureId],
    queryFn: async () => getLecture(lectureId, false)
  });

export const FilesQuery = (path: string) =>
  queryOptions({
    queryKey: ['files', path],
    queryFn: async () => getFiles(path)
  });
