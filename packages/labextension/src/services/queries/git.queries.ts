import { RepoType } from '../../app/components/utils/repo-type';
import { queryOptions } from '@tanstack/react-query';
import { getRemoteFileStatus, getRemoteStatus } from '../git.service';
import { LectureDetailDto } from '../../model/lectureDetailDto';

export const remoteStatusQuery = (
  lecture: LectureDetailDto,
  assignmentId: number,
  repo: RepoType,
  reload = false
) =>
  queryOptions({
    queryKey: ['remote-repo-status', lecture.code, assignmentId, repo],
    queryFn: async () => {
      return await getRemoteStatus(lecture.id, assignmentId, repo, reload);
    }
  });

export const remoteFileStatusQuery = (
  lectureId: number,
  assignmentId: number,
  repo: RepoType,
  filePath: string,
  reload = false
) =>
  queryOptions({
    queryKey: ['remote-file-status', lectureId, assignmentId, repo, filePath],
    queryFn: async () => {
      return await getRemoteFileStatus(
        lectureId,
        assignmentId,
        repo,
        filePath,
        reload
      );
    }
  });
