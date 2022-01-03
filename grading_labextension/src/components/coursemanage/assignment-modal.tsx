import * as React from 'react';
import {
  Badge,
  BottomNavigation,
  BottomNavigationAction,
  Box,
  Paper
} from '@mui/material';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import { Assignment } from '../../model/assignment';
import { Lecture } from '../../model/lecture';
import { getAllSubmissions } from '../../services/submissions.service';
import { GradingComponent } from './grading';
import { AssignmentFileView } from './file-view';
import { Submission } from '../../model/submission';

export interface IAssignmentModalProps {
  lecture: Lecture;
  assignment: Assignment;
  latestSubmissions: Submission[];
}

export const AssignmentModalComponent = (props: IAssignmentModalProps) => {
  const [latestSubmissions, setSubmissions] = React.useState(
    props.latestSubmissions
  );
  const [navigation, setNavigation] = React.useState(0);

  return (
    <Box>
      {navigation == 0 && (
        <AssignmentFileView
          lecture={props.lecture}
          assignment={props.assignment}
          latest_submissions={latestSubmissions}
        />
      )}

      {navigation == 1 && (
        <GradingComponent
          lecture={props.lecture}
          assignment={props.assignment}
          latest_submissions={latestSubmissions}
        />
      )}

      <Paper
        sx={{ position: 'absolute', bottom: 0, left: 0, right: 0 }}
        elevation={3}
      >
        <BottomNavigation
          showLabels
          value={navigation}
          onChange={(event, newValue) => {
            console.log(newValue);
            setNavigation(newValue);
            getAllSubmissions(props.lecture, props.assignment, true, true).then(
              (response: any) => {
                setSubmissions(response);
              }
            );
          }}
        >
          <BottomNavigationAction label="Overview" icon={<MoreVertIcon />} />
          <BottomNavigationAction
            label="Submissions"
            icon={
              <Badge
                color="secondary"
                badgeContent={props.latestSubmissions?.length}
                showZero={props.latestSubmissions !== null}
              >
                <MoreVertIcon />
              </Badge>
            }
          />
        </BottomNavigation>
      </Paper>
    </Box>
  );
};