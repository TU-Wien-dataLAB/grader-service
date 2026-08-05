import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Assignment } from '../../../model/assignment';
import { updateAssignment } from '../../../services/assignments.service';
import { IAssignmentChecked } from '../../pages/instructor-view/lecture';
import { useMutationStatus } from '../../../widget';
import { HTTPError } from '../../../services/request.service';

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
    onError: (error: HTTPError, variables) =>
      setStatus({
        status: 'error',
        message: error?.message || variables.errorMessage
      })
  });

  const updateAssignmentStatus = (
    status: 'created' | 'released' | 'complete',
    assignment: Assignment,
    lectureId: number,
    success: string,
    error: string
  ) => {
    updateStatusMutation.mutate({
      status,
      assignment,
      lectureId,
      successMessage: success,
      errorMessage: error
    });
  };

  const handleRelease = (assignment: Assignment, lectureId: number) => {
    updateAssignmentStatus(
      'released',
      assignment,
      lectureId,
      assignment.status === 'complete'
        ? 'The assignment is no longer marked as complete.'
        : 'The assignment is now available to students.',
      'Error releasing assignment'
    );
  };

  const handleAssignmentsRelease = (
    assignmentsChecked: IAssignmentChecked[],
    lectureId: number
  ) => {
    assignmentsChecked.map(
      a => a.checked && handleRelease(a.assignment, lectureId)
    );
  };
  const handleUnrelease = (assignment: Assignment, lectureId: number) => {
    updateAssignmentStatus(
      'created',
      assignment,
      lectureId,
      'This assignment is no longer available to students.',
      'Error unreleasing assignment'
    );
  };

  const handleComplete = (assignment: Assignment, lectureId: number) => {
    updateAssignmentStatus(
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
