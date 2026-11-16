import { useQuery } from '@tanstack/react-query';
import {
  getFiles,
  lectureBasePath
} from '../../../services/local-file.service';
import { getRemoteStatus } from '../../../services/git.service';
import { lectureQuery } from '../../../services/queries/lectures.queries';
import { RepoType } from '../../components/utils/repo-type';

/**
 * Queries the number of local files and the remote status of the source repo
 * of the given assignment. Both are needed to render the release badges.
 * The remote status is only queried if there are local files at all.
 */
export function useAssignmentRemoteStatus(
  lectureId: number,
  assignmentId: number | undefined,
  enabled = true
) {
  const { data: lecture } = useQuery(lectureQuery(lectureId));
  const { data: filesLength } = useQuery({
    queryKey: ['files-length', lecture?.code, assignmentId, 'source'],
    queryFn: async () => {
      return await getFiles(
        `${lectureBasePath}${lecture.code}/source/${assignmentId}`
      ).then(files => files?.length);
    },
    enabled: enabled && !!lecture && assignmentId !== undefined
  });
  const { data: remoteRepoStatus } = useQuery({
    queryKey: ['remote-repo-status', lecture?.code, assignmentId, 'source'],
    queryFn: async () => {
      return await getRemoteStatus(lectureId, assignmentId!, RepoType.SOURCE);
    },
    enabled: !!filesLength
  });
  return {
    filesLength,
    remoteStatus: remoteRepoStatus?.status
  };
}
