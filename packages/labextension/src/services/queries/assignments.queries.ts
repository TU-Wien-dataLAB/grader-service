import { getAllAssignments, getAssignment } from '../assignments.service';
import { queryOptions } from '@tanstack/react-query';

export const assignmentsQuery = (lectureId: number) =>
  queryOptions({
    queryKey: ['assignments', lectureId],
    queryFn: async () => getAllAssignments(lectureId, false, false)
  });

export const assignmentQuery = (lectureId: number, assignmentId: number) =>
  queryOptions({
    queryKey: ['assignments', lectureId, assignmentId],
    queryFn: async () => getAssignment(lectureId, assignmentId, false)
  });
