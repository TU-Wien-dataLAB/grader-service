import { Box } from '@mui/material';
import { Files } from './files';
import * as React from 'react';
import { useRouteLoaderData } from 'react-router-dom';
import { Lecture } from '../../../model/lecture';
import { Assignment } from '../../../model/assignment';
import { Submission } from '../../../model/submission';

export const FileView = () => {
  const { lecture, assignments, users } = useRouteLoaderData('lecture') as {
    lecture: Lecture,
    assignments: Assignment[],
    users: { instructors: string[], tutors: string[], students: string[] }
  };
  const { assignment, allSubmissions, latestSubmissions } = useRouteLoaderData('assignment') as {
    assignment: Assignment,
    allSubmissions: Submission[],
    latestSubmissions: Submission[]
  };

  const [assignmentState, setAssignmentState] = React.useState(assignment);
  const onAssignmentChange = (assignment: Assignment) => {
    setAssignmentState(assignment);
  };


  return (
    <Files 
        lecture={lecture}
        assignment={assignmentState}
        onAssignmentChange={onAssignmentChange} />
   
)};