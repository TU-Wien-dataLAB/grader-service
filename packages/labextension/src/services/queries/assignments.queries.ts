import { getAllAssignments } from '../assignments.service';

export const assignmentsQuery = (lectureId: number) => ({
  queryKey: ['assignments', lectureId],
  queryFn: async () => getAllAssignments(lectureId, false, false)
});
