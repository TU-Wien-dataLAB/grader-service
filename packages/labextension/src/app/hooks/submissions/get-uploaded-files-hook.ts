import { useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { GlobalObjects } from '../../../index';
import { getFiles } from '../../../services/local-file.service';

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

  return useQuery({
    queryKey,
    queryFn: () => getFiles(path),
    enabled: !!path
  });
};
