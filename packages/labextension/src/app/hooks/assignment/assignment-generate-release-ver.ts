import { useMutation, useQueryClient } from '@tanstack/react-query';
import { generateAssignment } from '../../../services/assignments.service';
import { useMutationStatus } from '../../../widget';
import { HTTPError } from '../../../services/request.service';
import { RepoType } from '../../components/utils/repo-type';
import { LectureDetailDto } from '../../../model/lectureDetailDto';

export function useAssignmentGenerateReleaseVer() {
  const queryClient = useQueryClient();
  const { setStatus } = useMutationStatus();
  const generateAssignmentReleaseVerMutation = useMutation({
    mutationFn: async (variables: {
      assignmentId: number;
      lecture: LectureDetailDto;
    }) => {
      await generateAssignment(variables.lecture.id, variables.assignmentId);
    },
    onSuccess: async (data, variables) => {
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: [
            'files',
            variables.lecture.code,
            variables.assignmentId,
            'release'
          ]
        }),
        queryClient.invalidateQueries({
          queryKey: [
            'remote-repo-status',
            variables.lecture.code,
            variables.assignmentId,
            RepoType.RELEASE
          ]
        })
      ]);
      setStatus({
        status: 'success',
        message: 'Successfully created student version of the assignment!'
      });
    },
    onError: (error: HTTPError) =>
      setStatus({
        status: 'error',
        message:
          error?.message || 'Error creating student version of the assignment.'
      })
  });

  const handleGenerateAssignmentReleaseVer = (
    lecture: LectureDetailDto,
    assignmentId: number
  ) => {
    generateAssignmentReleaseVerMutation.mutate({ assignmentId, lecture });
  };
  return { handleGenerateAssignmentReleaseVer };
}
