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
import { Lecture } from '../../../model/lecture';
import { Submission } from '../../../model/submission';
import GroupIcon from '@mui/icons-material/Group';
import ChecklistIcon from '@mui/icons-material/Checklist';
import GradeIcon from '@mui/icons-material/Grade';
import QuestionMarkIcon from '@mui/icons-material/QuestionMark';

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
    <Grid container rowSpacing={1} columnSpacing={{ xs: 1, sm: 2, md: 3 }}>
      <Grid item xs={6}>
        <Card elevation={3}
            sx={{minWidth: "150px"}}>
          <CardHeader title='Students'/>
          <CardContent
            sx={{
              alignItems: { xs: 'center' },
              overflowY: 'auto'
            }}
          >
          <GroupIcon color="primary" sx={{ fontSize: 80, ml: 1}}/>
          <Typography sx={{ fontSize: 13, mr: 0.5, ml: 0.5}}>
            {'Overall number of students in this lecture: '}
          </Typography>
          <Typography color="text.secondary" sx={{ml: 0.5, fontSize: 13}}> 
            {props.users?.students.length} 
          </Typography>
         </CardContent>
        </Card>
        
      </Grid>
      <Grid item xs={6}>
        <Card elevation={3}
            sx={{minWidth: "150px"}}>
          <CardHeader title='Submissions'/>
          <CardContent
            sx={{
              alignItems: { xs: 'center' },
              overflowY: 'auto'
            }}
          >
          <ChecklistIcon color="primary" sx={{ fontSize: 80, ml: 1}}/>
          <Typography sx={{ fontSize: 13, mr: 0.5, ml: 0.5}}>
            {'Total number of submissions: '}
          </Typography>
          <Typography color="text.secondary" sx={{ml: 0.5, fontSize: 13}}> 
            {props.allSubmissions.length} 
          </Typography>
         </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12}>
        <Divider/>
      </Grid>
      <Grid item xs={6}>
        <Card elevation={3}
            sx={{minWidth: "150px"}}>
          <CardHeader title='Grading behaviour'/>
          <CardContent
            sx={{
              alignItems: { xs: 'center' },
              overflowY: 'auto'
            }}
          >
          <GradeIcon color="primary" sx={{ fontSize: 80, ml: 1}}/>
          <Typography sx={{ fontSize: 13, mr: 0.5, ml: 0.5}}>
            {gradingBehaviour}
          </Typography>
      
         </CardContent>
        </Card>
      </Grid>
      <Grid item xs={6}>
        <Card elevation={3}
            sx={{minWidth: "150px"}}>
          <CardHeader title='Assignment type'/>
          <CardContent
            sx={{
              alignItems: { xs: 'center' },
              overflowY: 'auto'
            }}
          >
          <QuestionMarkIcon color="primary" sx={{ fontSize: 80, ml: 1}}/>
          <Typography sx={{ fontSize: 13, mr: 0.5, ml: 0.5}}>
            {props.assignment.type === 'user' ? 'User' : 'Group'}
          </Typography>
      
         </CardContent>
        </Card>
      </Grid>

    </Grid>
    
  );
};
