import { Box, Grid } from '@mui/material';
import { SectionTitle } from '../../util/section-title';
import { Files } from './files';
import * as React from 'react';
import { getGitLog, IGitLogObject } from '../../../services/file.service';
import { RepoType } from '../../util/repo-type';
import { useRouteLoaderData } from 'react-router-dom';
import { Lecture } from '../../../model/lecture';
import { Assignment } from '../../../model/assignment';
import { Submission } from '../../../model/submission';
import { submissionsReducer } from '../reducers';

export const FileView = () => {
    const { lecture, assignments } = useRouteLoaderData('lecture') as {
        lecture: Lecture,
        assignments: Assignment[]
    };
    const { assignment, allSubmissions, latestSubmissions } = useRouteLoaderData('assignment') as {
        assignment: Assignment,
        allSubmissions: Submission[],
        latestSubmissions: Submission[]
    };

    const [assignmentState, setAssignmentState] = React.useState<Assignment>(assignment);
    const [submissionsState, setSubmissions] = React.useState<Submission[]>(latestSubmissions);


    return <Box>
      <SectionTitle title={'Files'}></SectionTitle>   
      <Box sx={{ ml: 3, mr: 3, mb: 3, mt: 3 }}>
      <Grid container spacing={2} alignItems='stretch'>
        <Grid item xs={12} md={6} lg={5}>
          <Files
            lecture={lecture}
            assignment={assignmentState}
            />
        </Grid>
      </Grid>
    </Box>
  </Box>;
};
      
