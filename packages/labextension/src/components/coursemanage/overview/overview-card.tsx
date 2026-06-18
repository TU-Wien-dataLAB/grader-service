// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import {
  Divider,
  Paper,
  Typography,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText
} from '@mui/material';
import * as React from 'react';
import { Assignment } from '../../../model/assignment';
import { Lecture } from '../../../model/lecture';
import GroupIcon from '@mui/icons-material/Group';
import ChecklistIcon from '@mui/icons-material/Checklist';
import GradeIcon from '@mui/icons-material/Grade';
import { AssignmentSettings } from '../../../model/assignmentSettings';

export interface IOverviewCardProps {
  lecture: Lecture;
  assignment: Assignment;
  latestSubmissions: number;
  students: number;
}

export const OverviewCard = (props: IOverviewCardProps) => {
  const gradingBehaviour =
    props.assignment.settings.autograde_type ===
    AssignmentSettings.AutogradeTypeEnum.Auto
      ? 'Automatic Grading'
      : props.assignment.settings.autograde_type ===
          AssignmentSettings.AutogradeTypeEnum.FullAuto
        ? 'Fully Automatic Grading'
        : 'No Automatic Grading';

  return (
    <Paper
      elevation={3}
      sx={{
        padding: 3,
        borderRadius: 2,
        width: '100%',
        margin: '0 auto'
      }}
    >
      <Typography
        variant="h5"
        sx={{ mb: 2, fontWeight: 'bold', textAlign: 'center' }}
      >
        Assignment Information
      </Typography>
      <Divider sx={{ mb: 2 }} />
      <List>
        <ListItem>
          <ListItemAvatar>
            <GroupIcon color="primary" sx={{ fontSize: 40 }} />
          </ListItemAvatar>
          <ListItemText
            primary="Students"
            secondary={`Overall number of students in this lecture: ${props.students}`}
          />
        </ListItem>
        <Divider variant="inset" />
        <ListItem>
          <ListItemAvatar>
            <ChecklistIcon color="primary" sx={{ fontSize: 40 }} />
          </ListItemAvatar>
          <ListItemText
            primary="Submissions"
            secondary={`Number of students that have submitted: ${props.latestSubmissions}`}
          />
        </ListItem>
        <Divider variant="inset" />
        <ListItem>
          <ListItemAvatar>
            <GradeIcon color="primary" sx={{ fontSize: 40 }} />
          </ListItemAvatar>
          <ListItemText
            primary="Grading Behaviour"
            secondary={gradingBehaviour}
          />
        </ListItem>
      </List>
    </Paper>
  );
};
