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
import MoreVertIcon from '@mui/icons-material/MoreVert';
import { Assignment } from '../../model/assignment';
import { Lecture } from '../../model/lecture';
import { getAllSubmissions } from '../../services/submissions.service';
import { GradingComponent } from './grading-view/grading';
import { OverviewComponent } from './overview-view/overview';
import { Submission } from '../../model/submission';

export interface IAssignmentModalProps {
  lecture: Lecture;
  assignment: Assignment;
  allSubmissions: any[];
  latestSubmissions: Submission[];
  root: HTMLElement;
  users: any;
  onClose: () => void;
}

export const AssignmentModalComponent = (props: IAssignmentModalProps) => {
  const [latestSubmissions, setSubmissions] = React.useState(
    props.latestSubmissions
  );
  const [navigation, setNavigation] = React.useState(0);

  return (
    <Box>
      <Box
        sx={{
          position: 'absolute',
          bottom: 58,
          top: 0,
          left: 0,
          right: 0,
          overflowY: 'auto'
        }}
      >
        {navigation === 0 && (
          <OverviewComponent
            lecture={props.lecture}
            assignment={props.assignment}
            allSubmissions={props.allSubmissions}
            latest_submissions={latestSubmissions}
            users={props.users}
            onClose={props.onClose}
          />
        )}

        {navigation === 1 && (
          <GradingComponent
            lecture={props.lecture}
            assignment={props.assignment}
            allSubmissions={props.allSubmissions}
            root={props.root}
          />
        )}
      </Box>

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
            getAllSubmissions(
              props.lecture,
              props.assignment,
              'latest',
              true
            ).then((response: any) => {
              setSubmissions(response);
            });
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
