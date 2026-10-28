import React, { useState } from 'react';
import NewSubmission from './new-submission';
import { SubmissionsView } from './submissions-view';

export type TSubmissionStates = 'view' | 'create-form' | 'edit-form';

interface ISubmissionsProps {
  lectureId: number;
  assignmentId: number;
}

const Submissions = ({ lectureId, assignmentId }: ISubmissionsProps) => {
  const [openNewSubmission, setOpenNewSubmission] = useState<boolean>(false);

  return (
    <div>
      {openNewSubmission ? (
        <NewSubmission
          assignmentId={assignmentId}
          lectureId={lectureId}
          setOpenNewSubmission={setOpenNewSubmission}
        />
      ) : (
        <SubmissionsView
          assignmentId={assignmentId}
          lectureId={lectureId}
          setOpenNewSubmission={setOpenNewSubmission}
        />
      )}
    </div>
  );
};

export default Submissions;
