import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Assignment } from '../../../model/assignment';
import { updateAssignment } from '../../../services/assignments.service';
import { IAssignmentChecked } from '../../pages/instructor-view/lecture';
import { useMutationStatus } from '../../../widget';

export function useAssignmentStatus() {
  const queryClient = useQueryClient();
  const { setStatus } = useMutationStatus();
  const updateStatusMutation = useMutation({
    mutationFn: async (variables: {
      status: 'created' | 'released' | 'complete';
      assignment: Assignment;
      lectureId: number;
      successMessage: string;
      errorMessage: string;
    }) => {
      const updatedAssignment = {
        ...variables.assignment,
        status: variables.status
      };
      return updateAssignment(variables.lectureId, updatedAssignment);
    },
    onSuccess: async (data, variables) => {
      await queryClient.invalidateQueries({
        queryKey: ['assignments', variables.lectureId]
      });
      setStatus({
        status: 'success',
        message: variables.successMessage
      });
    },
    onError: (error: any, variables) =>
      setStatus({
        status: 'error',
        message: error.message || error.error.message || variables.errorMessage
      })
  });

  const updateAssignmentStatus = async (
    status: 'created' | 'released' | 'complete',
    assignment: Assignment,
    lectureId: number,
    success: string,
    error: string
  ) => {
    try {
      await updateStatusMutation.mutateAsync({
        status,
        assignment,
        lectureId,
        successMessage: success,
        errorMessage: error
      });
    } catch (error) {
      setStatus({
        message: 'Error updating assignment status: ' + error,
        status: 'error'
      });
    }
  };

  const handleRelease = async (assignment: Assignment, lectureId: number) => {
    await updateAssignmentStatus(
      'released',
      assignment,
      lectureId,
      assignment.status === 'complete'
        ? 'The assignment is no longer marked as complete.'
        : 'The assignment is now available to students.',
      'Error releasing assignment'
    );
  };

  const handleAssignmentsRelease = async (
    assignmentsChecked: IAssignmentChecked[],
    lectureId: number
  ) => {
    assignmentsChecked.map(
      async a => a.checked && (await handleRelease(a.assignment, lectureId))
    );
  };
  const handleUnrelease = async (assignment: Assignment, lectureId: number) => {
    await updateAssignmentStatus(
      'created',
      assignment,
      lectureId,
      'This assignment is no longer marked as released.',
      'Error unreleasing assignment'
    );
  };

  const handleComplete = async (assignment: Assignment, lectureId: number) => {
    await updateAssignmentStatus(
      'complete',
      assignment,
      lectureId,
      'This assignment was marked as complete.',
      'Error completing assignment'
    );
  };
  return {
    handleRelease,
    handleAssignmentsRelease,
    handleUnrelease,
    handleComplete
  };
}
