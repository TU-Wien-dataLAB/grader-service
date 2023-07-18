import { Box, Grid } from '@mui/material';
import { SectionTitle } from '../../util/section-title';
import { AssignmentStatus } from '../overview/assignment-status';
import { OverviewCard } from '../overview/overview-card';
import { Files } from './files';
import { GitLog } from './git-log';
import * as React from 'react';
import { getGitLog, IGitLogObject } from '../../../services/file.service';
import { RepoType } from '../../util/repo-type';
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
  const [gitLogs, setGitLog] = React.useState([] as IGitLogObject[]);

  const onAssignmentChange = (assignment: Assignment) => {
    setAssignmentState(assignment);
  };
  const updateGitLog = () => {
    getGitLog(lecture, assignment, RepoType.SOURCE, 10).then(logs =>
      setGitLog(logs)
    );
  };

  React.useEffect(() => {
    updateGitLog();
  }, [assignmentState]);

  return <Box>
    <SectionTitle title={'Files'}></SectionTitle>
    <Box sx={{ ml: 3, mr: 3, mb: 3, mt: 3 }}>
      <Grid container spacing={2} alignItems='stretch'>
        <Grid item xs={12} md={6} lg={5}>
          <Files
            lecture={lecture}
            assignment={assignmentState}
            onAssignmentChange={onAssignmentChange}
            updateGitLog={updateGitLog}
          />
        </Grid>
        <Grid item xs={12} md={6} lg={4}>
          <GitLog gitLogs={gitLogs} />
        </Grid>
      </Grid>
    </Box>
  </Box>;
};