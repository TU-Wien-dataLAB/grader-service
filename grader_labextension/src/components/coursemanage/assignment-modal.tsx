// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import * as React from 'react';
import {
  Badge,
  BottomNavigation,
  BottomNavigationAction,
  Box,
  Paper
} from '@mui/material';
import DashboardIcon from '@mui/icons-material/Dashboard';
import FormatListNumberedIcon from '@mui/icons-material/FormatListNumbered';
import QueryStatsIcon from '@mui/icons-material/QueryStats';
import SettingsIcon from '@mui/icons-material/Settings';
import { Assignment } from '../../model/assignment';
import { Lecture } from '../../model/lecture';
import { getAllSubmissions } from '../../services/submissions.service';
import { GradingComponent } from './grading/grading';
import { OverviewComponent } from './overview/overview';
import { Submission } from '../../model/submission';
import { StatsComponent } from './stats/stats';
import { GradeBook } from '../../services/gradebook';
import { loadNumber, storeNumber } from '../../services/storage.service';
import { SettingsComponent } from './settings/settings';
import {
  useRouteLoaderData,
  Outlet,
  Link,
  matchPath,
  useLocation,
  useParams,
  useMatch,
  useMatches
} from 'react-router-dom';

export interface IAssignmentModalProps {
  root: HTMLElement;
}

export const AssignmentModalComponent = (props: IAssignmentModalProps) => {
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

  const params = useParams();
  const match = useMatch(`/lecture/${params.lid}/assignment/${params.aid}/*`);
  const tab = match.params['*'];
  console.log(tab)

  // const [navigation, setNavigation] = React.useState(0);
  // Note: maybe this should be done with handles as well
  let navigation = -1;
  if (tab === "") {
    navigation = 0;
  } else if (tab.indexOf('submissions') !== -1) {
    navigation = 1;
  } else if (tab.indexOf('stats') !== -1) {
    navigation = 2;
  } else if (tab.indexOf('settings') !== -1) {
    navigation = 3;
  } else {
    throw 'incorrect tab name';
  }

  console.log(navigation)


  // TODO: fix layout of content and navigation! The absolute positioning of the boxes leads to unresponsive breadcrumbs because the box is at top:0
  //  no magic numbers anymore!
  return (
    <Box>
      <Box
        sx={{
          position: 'absolute',
          bottom: 58,
          top: 25,
          left: 0,
          right: 0,
          overflowY: 'auto'
        }}
      >
        <Outlet />
        { /*


        {navigation === 3 && (
          <SettingsComponent
            assignment={assignment}
            lecture={lecture}
            submissions={latestSubmissions}
          />
        )}
        */}

      </Box>

      <Paper
        sx={{ position: 'absolute', bottom: 0, left: 0, right: 0 }}
        elevation={3}
      >
        <BottomNavigation
          showLabels
          value={navigation}
        >
          <BottomNavigationAction label='Overview' icon={<DashboardIcon />} component={Link as any} to={''} />
          <BottomNavigationAction
            label='Submissions'
            icon={
              <Badge
                color='secondary'
                badgeContent={latestSubmissions?.length}
                showZero={latestSubmissions !== null}
              >
                <FormatListNumberedIcon />
              </Badge>
            }
            component={Link as any} to={'submissions'}
          />
          <BottomNavigationAction label='Stats' icon={<QueryStatsIcon />} component={Link as any} to={'stats'} />
          <BottomNavigationAction label='Settings' icon={<SettingsIcon />} component={Link as any} to={'settings'} />
        </BottomNavigation>
      </Paper>
    </Box>
  );
};
