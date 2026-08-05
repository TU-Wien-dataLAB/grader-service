import { useMutation, useQueryClient } from '@tanstack/react-query';
import { deleteAssignment } from '../../../services/assignments.service';
import { useMutationStatus } from '../../../widget';
import { HTTPError } from '../../../services/request.service';

export function useAssignmentDelete() {
  const queryClient = useQueryClient();
  const { setStatus } = useMutationStatus();
  const deleteAssignmentMutation = useMutation({
    mutationFn: async (variables: {
      assignmentId: number;
      lectureId: number;
    }) => {
      await deleteAssignment(variables.lectureId, variables.assignmentId);
    },
    onSuccess: async (data, variables) => {
      await queryClient.invalidateQueries({
        queryKey: ['assignments', variables.lectureId]
      });
      setStatus({
        status: 'success',
        message: 'Successfully deleted assignment!'
      });
    },
    onError: (error: HTTPError) =>
      setStatus({
        status: 'error',
        message: error?.message || 'Error deleting assignment.'
      })
  });

  const handleDeleteAssignment = (assignmentId: number, lectureId: number) => {
    deleteAssignmentMutation.mutate({ assignmentId, lectureId });
  };
  return { handleDeleteAssignment };
}
