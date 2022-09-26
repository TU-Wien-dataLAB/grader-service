import { Lecture } from '../../../model/lecture';
import { Assignment } from '../../../model/assignment';
import { Submission } from '../../../model/submission';
import { Box, Grid, IconButton, Tooltip } from '@mui/material';
import { ModalTitle } from '../../util/modal-title';
import ReplayIcon from '@mui/icons-material/Replay';
import * as React from 'react';
import { getAllSubmissions } from '../../../services/submissions.service';
import { SubmissionTimeSeries } from './submission-timeseries';
import { GradingProgress } from './grading-progress';
import { StudentSubmissions } from './student-submissions';
import { ScoreDistribution } from './score-distribution';
import { getUsers } from '../../../services/lectures.service';
import { GradeBook } from '../../../services/gradebook';
import { AssignmentScore } from './assignment-score';
import { getAssignmentProperties } from '../../../services/assignments.service';

export const filterUserSubmissions = (
  submissions: Submission[],
  users: string[]
): Submission[] => {
  return submissions.filter((v, i, a) => !users.includes(v.username));
};

export interface IStatsProps {
  lecture: Lecture;
  assignment: Assignment;
  allSubmissions: Submission[];
  latestSubmissions: Submission[];
  users: { students: string[]; tutors: string[]; instructors: string[] };
  root: HTMLElement;
}

export const StatsComponent = (props: IStatsProps) => {
  const [submissions, setSubmissions] = React.useState(props.allSubmissions);
  const [latestSubmissions, setLatestSubmissions] = React.useState(
    props.latestSubmissions
  );
  const [gb, setGb] = React.useState(null as GradeBook);
  const [users, setUsers] = React.useState(props.users);

  const updateSubmissions = async () => {
    setSubmissions(
      await getAllSubmissions(props.lecture, props.assignment, 'none', true)
    );
    setLatestSubmissions(
      await getAllSubmissions(props.lecture, props.assignment, 'latest', true)
    );
    setUsers(await getUsers(props.lecture));
    setGb(
      new GradeBook(
        await getAssignmentProperties(props.lecture.id, props.assignment.id)
      )
    );
  };

  React.useEffect(() => {
    getAllSubmissions(props.lecture, props.assignment, 'none', true).then(
      response => {
        setSubmissions(response);
      }
    );
    getAllSubmissions(props.lecture, props.assignment, 'latest', true).then(
      response => {
        setLatestSubmissions(response);
      }
    );
  }, [props.allSubmissions, props.latestSubmissions]);

  React.useEffect(() => {
    getUsers(props.lecture).then(response => {
      setUsers(response);
    });
  }, [props.users]);

  React.useEffect(() => {
    getAssignmentProperties(props.lecture.id, props.assignment.id).then(
      properties => {
        setGb(new GradeBook(properties));
      }
    );
  }, []);

  return (
    <Box>
      <ModalTitle title={`${props.assignment.name} Stats`}>
        <Box sx={{ ml: 2 }} display="inline-block">
          <Tooltip title="Reload">
            <IconButton aria-label="reload" onClick={updateSubmissions}>
              <ReplayIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </ModalTitle>
      <Box sx={{ ml: 3, mr: 3, mb: 3, mt: 3 }}>
        <Grid container spacing={2} alignItems="stretch">
          <Grid item xs={12}>
            <SubmissionTimeSeries
              lecture={props.lecture}
              assignment={props.assignment}
              allSubmissions={submissions}
              latestSubmissions={latestSubmissions}
              users={users}
              root={props.root}
            />
          </Grid>
          <Grid item xs={4}>
            <GradingProgress
              lecture={props.lecture}
              assignment={props.assignment}
              allSubmissions={submissions}
              latestSubmissions={latestSubmissions}
              users={users}
              root={props.root}
            />
          </Grid>
          <Grid item xs={4}>
            <StudentSubmissions
              lecture={props.lecture}
              assignment={props.assignment}
              allSubmissions={submissions}
              latestSubmissions={latestSubmissions}
              users={users}
              root={props.root}
            />
          </Grid>
          <Grid item xs={4}>
            <AssignmentScore gb={gb} />
          </Grid>
          <Grid item xs={12}>
            <ScoreDistribution
              lecture={props.lecture}
              assignment={props.assignment}
              allSubmissions={submissions}
              latestSubmissions={latestSubmissions}
              users={users}
              root={props.root}
            />
          </Grid>
        </Grid>
      </Box>
    </Box>
  );
};
