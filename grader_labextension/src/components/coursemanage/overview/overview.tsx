// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import * as React from 'react';

import { Assignment } from '../../../model/assignment';
import { Lecture } from '../../../model/lecture';
import { SectionTitle } from '../../util/section-title';
import { OverviewCard } from './overview-card';
import { Box, Grid } from '@mui/material';
import { AssignmentStatus } from './assignment-status';
import { Submission } from '../../../model/submission';
import { useRouteLoaderData } from 'react-router-dom';
import { breakpoints } from '@mui/system';
import { useEffect, useState } from 'react';


export const OverviewComponent = () => {
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

  const [windowSize, setWindowSize] = useState([
    window.innerWidth,
    window.innerHeight,
  ]);

  useEffect(() => {
    const handleWindowResize = () => {
      setWindowSize([window.innerWidth, window.innerHeight]);
    };

    window.addEventListener('resize', handleWindowResize);

    return () => {
      window.removeEventListener('resize', handleWindowResize);
    };
  }, []);
  
  return (
    <Box>
      <SectionTitle title={assignmentState.name}></SectionTitle>
      <Box sx={{ ml: 3, mr: 3, mb: 3, mt: 3}}>
        <Grid container spacing={3} alignItems='stretch'>
          <Grid item xs={7}>
          <AssignmentStatus
              lecture={lecture}
              assignment={assignmentState}
              onAssignmentChange={onAssignmentChange}
            />
          </Grid>
          <Grid item xs = {windowSize[0]>=2000 ? 3 : 5}>
          <OverviewCard
              lecture={lecture}
              assignment={assignmentState}
              allSubmissions={allSubmissions}
              latestSubmissions={latestSubmissions}
              users={users}
            />
          </Grid>
        </Grid>
      </Box>
    </Box>
  );
};
