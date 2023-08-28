import { Lecture } from '../../../model/lecture';
import { Assignment } from '../../../model/assignment';
import { Submission } from '../../../model/submission';
import { Box, IconButton, Tooltip } from '@mui/material';
import Grid from '@mui/material/Unstable_Grid2';
import { SectionTitle } from '../../util/section-title';
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
import { useRouteLoaderData } from 'react-router-dom';

export const filterUserSubmissions = (
  submissions: Submission[],
  users: string[]
): Submission[] => {
  return submissions.filter((v, i, a) => !users.includes(v.username));
};

export interface IStatsSubComponentProps {
  lecture: Lecture;
  assignment: Assignment;
  allSubmissions: Submission[];
  latestSubmissions: Submission[];
  users: { students: string[]; tutors: string[]; instructors: string[] };
}

export const StatsComponent = () => {
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

  const [allSubmissionsState, setAllSubmissionsState] = React.useState(allSubmissions);
  const [latestSubmissionsState, setLatestSubmissionsState] = React.useState(latestSubmissions);
  const [gb, setGb] = React.useState(null as GradeBook);
  const [usersState, setUsersState] = React.useState(users);

  const updateSubmissions = async () => {
    setAllSubmissionsState(
      await getAllSubmissions(lecture.id, assignment.id, 'none', true)
    );
    setLatestSubmissionsState(
      await getAllSubmissions(lecture.id, assignment.id, 'latest', true)
    );
    setUsersState(await getUsers(lecture.id));
    setGb(
      new GradeBook(
        await getAssignmentProperties(lecture.id, assignment.id)
      )
    );
  };

  React.useEffect(() => {
    getAllSubmissions(lecture.id, assignment.id, 'none', true).then(
      response => {
        setAllSubmissionsState(response);
      }
    );
    getAllSubmissions(lecture.id, assignment.id, 'latest', true).then(
      response => {
        setLatestSubmissionsState(response);
      }
    );
  }, [allSubmissions, latestSubmissions]);

  React.useEffect(() => {
    getUsers(lecture.id).then(response => {
      setUsersState(response);
    });
  }, [users]);

  React.useEffect(() => {
    getAssignmentProperties(lecture.id, assignment.id).then(
      properties => {
        setGb(new GradeBook(properties));
      }
    );
  }, []);

  return (
    <Box sx={{ flex: 1, overflow: 'auto'}}>
      <SectionTitle title={`${assignment.name} Stats`}>
        <Box sx={{ ml: 2 }} display='inline-block'>
          <Tooltip title='Reload'>
            <IconButton aria-label='reload' onClick={updateSubmissions}>
              <ReplayIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </SectionTitle>
      <Box sx={{ ml: 3, mr: 3, mb: 3, mt: 3 }}>
        <Grid container spacing={2} alignItems='stretch'>
          <Grid xs={12}>
            <SubmissionTimeSeries
              lecture={lecture}
              assignment={assignment}
              allSubmissions={allSubmissionsState}
              latestSubmissions={latestSubmissionsState}
              users={usersState}
            />
          </Grid>
          <Grid md={12} lg={4}>
            <GradingProgress
              lecture={lecture}
              assignment={assignment}
              allSubmissions={allSubmissionsState}
              latestSubmissions={latestSubmissionsState}
              users={usersState}
            />
          </Grid>
          <Grid md={12} lg={4}>
            <StudentSubmissions
              lecture={lecture}
              assignment={assignment}
              allSubmissions={allSubmissionsState}
              latestSubmissions={latestSubmissionsState}
              users={usersState}
            />
          </Grid>
          <Grid md={12} lg={4}>
            <AssignmentScore gb={gb} />
          </Grid>
          <Grid xs={12}>
            <ScoreDistribution
              lecture={lecture}
              assignment={assignment}
              allSubmissions={allSubmissionsState}
              latestSubmissions={latestSubmissionsState}
              users={usersState}
            />
          </Grid>
        </Grid>
      </Box>
    </Box>
  );
};
