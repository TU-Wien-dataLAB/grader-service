import { HTTPMethod, request } from './request.service';
import { Lecture } from '../model/lecture';
import { Assignment } from '../model/assignment';

export const syncSubmissions = (lecture: Lecture, assignment: Assignment) => {
  return request(
    HTTPMethod.PUT,
    `/lectures/${lecture.id}/assignments/${assignment.id}/sync`
  );
};
