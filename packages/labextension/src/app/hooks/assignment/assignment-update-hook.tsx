import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Assignment } from '../../../model/assignment';
import { updateAssignment } from '../../../services/assignments.service';
import { useMutationStatus } from '../../../widget';
import { HTTPError } from '../../../services/request.service';

export function useAssignmentUpdate() {
  const queryClient = useQueryClient();
  const { setStatus } = useMutationStatus();

  const updateAssignmentMutate = useMutation({
    mutationFn: async (variables: {
      assignment: Assignment;
      updatedValues: Assignment;
      lectureId: number;
    }) => {
      const updatedAssignment = {
        ...variables.assignment,
        ...variables.updatedValues
      };
      await updateAssignment(variables.lectureId, updatedAssignment);
    },
    onSuccess: async (data, variables) => {
      await queryClient.invalidateQueries({
        queryKey: ['assignments', variables.lectureId]
      });
      setStatus({
        status: 'success',
        message: 'Your changes have been saved successfully.'
      });
    },
    onError: (error: HTTPError) =>
      setStatus({
        status: 'error',
        message: error?.message || 'Error updating assignment.'
      })
  });

  const handleUpdateAssignment = async (
    assignment: Assignment,
    updatedValues: Assignment,
    lectureId: number
  ) => {
    updateAssignmentMutate.mutate({
      assignment,
      updatedValues,
      lectureId
    });
  };

  return { handleUpdateAssignment };
}
