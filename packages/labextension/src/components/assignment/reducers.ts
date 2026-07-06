import { Submission } from '../../model/submission';

interface SubmissionsAction {
  type: 'add' | 'set_all';
  submission: Submission;
}

export const submissionsReducer = (
  submissions: Submission[],
  action: SubmissionsAction
): Submission[] => {
  switch (action.type) {
    case 'add': {
      submissions.push(action.submission);
      return submissions;
    }
    case 'set_all': {
      return submissions;
    }
    default:
      return submissions;
  }
};
