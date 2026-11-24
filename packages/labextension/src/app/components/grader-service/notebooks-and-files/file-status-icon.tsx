import { RepoType } from '../../utils/repo-type';
import { useQuery } from '@tanstack/react-query';
import { remoteFileStatusQuery } from '../../../../services/queries/git.queries';
import { RemoteFileStatus } from '../../../../model/remoteFileStatus';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger
} from '../../../shadcn-components/ui/tooltip';
import { CircleExclamationPoint } from 'lucide-react';
import React from 'react';
import { getRelativePath } from '../../../../services/local-file.service';
import { FileRow } from './files-table';
import { lectureQuery } from '../../../../services/queries/lectures.queries';

export const fileStatusIcon = (
  lectureId: number,
  assignmentId: number,
  repo: string,
  file: FileRow
) => {
  const { data: lecture } = useQuery(lectureQuery(lectureId));
  const { data: remoteFileStatus } = useQuery(
    remoteFileStatusQuery(
      lectureId,
      assignmentId,
      repo === 'source' ? RepoType.SOURCE : RepoType.RELEASE,
      getRelativePath(lecture.code, repo, assignmentId, file.path)
    )
  );
  switch (remoteFileStatus?.status) {
    case RemoteFileStatus.UnsavedChanges:
      return (
        <Tooltip>
          <TooltipTrigger
            render={
              <CircleExclamationPoint className={'size-4 text-yellow-400'} />
            }
          />
          <TooltipContent>
            <p>Unsaved changes</p>
          </TooltipContent>
        </Tooltip>
      );
    case RemoteFileStatus.Divergent:
      return (
        <Tooltip>
          <TooltipTrigger
            render={
              <CircleExclamationPoint className={'size-4 text-red-400'} />
            }
          />
          <TooltipContent>
            <p>Out of sync</p>
          </TooltipContent>
        </Tooltip>
      );
    case RemoteFileStatus.NoBackup:
      return (
        <Tooltip>
          <TooltipTrigger
            render={
              <CircleExclamationPoint className={'size-4 text-gray-400'} />
            }
          />
          <TooltipContent>
            <p>No backup</p>
          </TooltipContent>
        </Tooltip>
      );
  }
};
