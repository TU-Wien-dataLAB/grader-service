// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import {
  Card,
  CardContent,
  CardHeader,
  Divider,
  Grid,
  Typography
} from '@mui/material';
import * as React from 'react';
import { Assignment } from '../../../model/assignment';
import { DeadlineComponent } from '../../util/deadline';
import { Lecture } from '../../../model/lecture';
import { utcToLocal } from '../../../services/datetime.service';
import { Submission } from '../../../model/submission';

export interface IOverviewCardProps {
  lecture: Lecture;
  assignment: Assignment;
  allSubmissions: Submission[];
  latestSubmissions: Submission[];
  users: { students: string[]; tutors: string[]; instructors: string[] };
}

export const OverviewCard = (props: IOverviewCardProps) => {
  let gradingBehaviour = 'No Automatic Grading';
  if (
    props.assignment.automatic_grading === Assignment.AutomaticGradingEnum.Auto
  ) {
    gradingBehaviour = 'Automatic Grading';
  } else if (
    props.assignment.automatic_grading ===
    Assignment.AutomaticGradingEnum.FullAuto
  ) {
    gradingBehaviour = 'Fully Automatic Grading';
  }

  return (
    <Card elevation={3}>
      <CardHeader title="Overview" />
      <CardContent
        sx={{
          alignItems: { xs: 'center' },
          height: '243px',
          minWidth: '150px',
          overflowY: 'auto'
        }}
      >
        <Typography sx={{ fontSize: 15, mt: 0.5, ml: 0.5 }}>
          {props.users?.students.length}
          <Typography
            color="text.secondary"
            sx={{
              display: 'inline-block',
              ml: 0.75,
              fontSize: 13
            }}
          >
            {'Student' + (props.users?.students.length === 1 ? '' : 's')}
          </Typography>
        </Typography>

        <Typography sx={{ fontSize: 15, mt: 0.5, ml: 0.5 }}>
          {props.users?.tutors.length}
          <Typography
            color="text.secondary"
            sx={{
              display: 'inline-block',
              ml: 0.75,
              fontSize: 13
            }}
          >
            {'Tutor' + (props.users?.tutors.length === 1 ? '' : 's')}
          </Typography>
        </Typography>

        <Typography sx={{ fontSize: 15, mt: 0.5, ml: 0.5 }}>
          {props.users?.instructors.length}
          <Typography
            color="text.secondary"
            sx={{
              display: 'inline-block',
              ml: 0.75,
              fontSize: 13
            }}
          >
            {'Instructor' + (props.users?.instructors.length === 1 ? '' : 's')}
          </Typography>
        </Typography>

        <Typography sx={{ fontSize: 15, mt: 0.5, ml: 0.5 }}>
          {props.allSubmissions.length}
          <Typography
            color="text.secondary"
            sx={{
              display: 'inline-block',
              ml: 0.75,
              fontSize: 13
            }}
          >
            {'Submissions Total'}
          </Typography>
        </Typography>
        <Typography sx={{ fontSize: 15, mt: 0.5, ml: 0.5 }}>
          {props.latestSubmissions.length}
          <Typography
            color="text.secondary"
            sx={{
              display: 'inline-block',
              ml: 0.75,
              fontSize: 13
            }}
          >
            {'Users that submitted at least once'}
          </Typography>
        </Typography>
        <Divider sx={{ mt: 1, mb: 1 }} />
        <Typography
          color="text.secondary"
          sx={{
            display: 'inline-block',
            fontSize: 13,
            mb: -1,
            ml: 0.5
          }}
        >
          Grading Behaviour:
        </Typography>
        <Typography sx={{ fontSize: 15, ml: 0.5 }}>
          {gradingBehaviour}
        </Typography>

        <Typography
          color="text.secondary"
          sx={{
            display: 'inline-block',
            fontSize: 13,
            mt: 1,
            mb: -1,
            ml: 0.5
          }}
        >
          Assignment Type:
        </Typography>
        <Typography sx={{ fontSize: 15, ml: 0.5 }}>
          {props.assignment.type === 'user' ? 'User' : 'Group'}
        </Typography>
      </CardContent>
      <DeadlineComponent
        due_date={props.assignment.due_date}
        compact={false}
        component={'card'}
      />
    </Card>
  );
};
