import { useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { GlobalObjects } from '../../../index';
import { getFiles, IFile } from '../../../services/local-file.service';
import { TSubmissionDirectory } from '../../components/grader-service/submissions/submission-details-dialog';

// This hook syncs the uploaded files in File Browser

export const useFiles = (path: string) => {
  const queryClient = useQueryClient();
  const queryKey = ['files', path];

  useEffect(() => {
    const contents = GlobalObjects.docManager.services.contents;

    const onChanged = (_: unknown, change: any) => {
      const affected = [change.newValue?.path, change.oldValue?.path].filter(
        Boolean
      );
      if (affected.some((p: string) => p.startsWith(path))) {
        queryClient.invalidateQueries({ queryKey });
      }
    };

    contents.fileChanged.connect(onChanged);
    return () => {
      contents.fileChanged.disconnect(onChanged);
    };
  }, [path, queryClient]);

  return useQuery<(IFile | TSubmissionDirectory)[]>({
    queryKey,
    queryFn: () => (path ? getFiles(path) : Promise.resolve([])),
    enabled: !!path
  });
};
