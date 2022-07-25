import * as React from 'react';
import { DeadlineComponent } from '../../util/deadline';
import { getAllLectures } from '../../../services/lectures.service';
import { getAssignment } from '../../../services/assignments.service';
import { Box } from '@mui/material';

export interface IDeadlineWrapperProps {
  notebookPaths: string[];
}

/**
 * React Component which handles all request which are needed to get the assignment deadline
 * Why is this needed => we can not to the requests in the widget because the constructor can not handle async requests
 * There is probably a better way to do this
 * @param props props of the component
 */
export const DeadlineWrapper = (props: IDeadlineWrapperProps) => {
  const [lecture, setLecture] = React.useState(null);
  const [assignment, setAssignment] = React.useState(null);

  React.useEffect(() => {
    if (lecture === null) {
      getAllLectures().then(response => {
        const l = response.find(l => l.code === props.notebookPaths[0]);
        if (l === undefined) {
          return;
        }
        setLecture(l);
      });
    }
    if (lecture === null) {
      return;
    }
    getAssignment(lecture.id, +props.notebookPaths[1]).then(response => {
      setAssignment(response);
    });
  }, [lecture]);

  return (
    <Box>
      {assignment !== null ? (
        <DeadlineComponent
          due_date={assignment.due_date}
          compact={false}
          component={'chip'}
        />
      ) : null}
    </Box>
  );
};
