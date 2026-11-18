import { useMutation, useQueryClient } from '@tanstack/react-query';
import { generateAssignment } from '../../../services/assignments.service';
import { useMutationStatus } from '../../../widget';
import { HTTPError } from '../../../services/request.service';

export function useAssignmentGenerateReleaseVer() {
  const queryClient = useQueryClient();
  const { setStatus } = useMutationStatus();
  const generateAssignmentReleaseVerMutation = useMutation({
    mutationFn: async (variables: {
      assignmentId: number;
      lectureId: number;
    }) => {
      await generateAssignment(variables.lectureId, variables.assignmentId);
    },
    onSuccess: async (data, variables) => {
      await queryClient.invalidateQueries({
        queryKey: [
          'files',
          variables.lectureId,
          variables.assignmentId,
          'release'
        ]
      });
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
    lectureId: number,
    assignmentId: number
  ) => {
    generateAssignmentReleaseVerMutation.mutate({ assignmentId, lectureId });
  };
  return { handleGenerateAssignmentReleaseVer };
}
