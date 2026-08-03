import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Assignment } from '../../../model/assignment';
import { createAssignment } from '../../../services/assignments.service';
import { useMutationStatus } from '../../../widget';

export function useAssignmentCreate() {
  const queryClient = useQueryClient();
  const { setStatus } = useMutationStatus();

  const createAssignmentMutation = useMutation({
    mutationFn: async (variables: {
      assignment: Assignment;
      lectureId: number;
    }) => {
      await createAssignment(variables.lectureId, variables.assignment);
    },
    onSuccess: async (data, variables) => {
      await queryClient.invalidateQueries({
        queryKey: ['assignments', variables.lectureId]
      });
      setStatus({
        status: 'success',
        message: 'The assignment has been created successfully.'
      });
    },
    onError: (error: any) =>
      setStatus({
        status: 'error',
        message:
          error.message || error.error.message || 'Error creating assignment.'
      })
  });

  const handleCreateAssignment = async (
    assignment: Assignment,
    lectureId: number
  ) => {
    createAssignmentMutation.mutate({ assignment, lectureId });
  };
  return { handleCreateAssignment };
}
