// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import {
  Divider,
  Grid,
  Paper,
  Typography,
  createTheme
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
    <Grid container spacing={2}>
      <Grid item xs={6}>
        <Paper elevation={3}
            sx={{
                height: "205px",
                textAlign: "center",
                overflowY: 'auto',
                padding: "10px"}}>
          <Typography sx={{textAlign: "left", fontSize: 24}}>Students</Typography>
          
          <GroupIcon color="primary" sx={{ fontSize: 80, ml: 1}}/>
          <Typography  sx={{ textAlign: "left", mr: 0.5, ml: 0.5}}>
            {'Overall number of students in this lecture: ' + props.users?.students.length}
          </Typography>
        </Paper>
        
      </Grid>
      <Grid item xs={6}>
        <Paper elevation={3}
            sx={{
                height: "205px",
                textAlign: "center",
                overflowY: 'auto',
                padding: "10px"}}>
          <Typography  sx={{textAlign: "left", fontSize: 24}}>Submissions</Typography>
          <ChecklistIcon color="primary" sx={{ fontSize: 80, ml: 1}}/>
          <Typography  sx={{ textAlign: "left", mr: 0.5, ml: 0.5}}>
            {'Total number of submissions: ' + props.allSubmissions.length}
          </Typography>
        </Paper>
      </Grid>
      <Grid item xs={12}>
        <Divider/>
      </Grid>
      <Grid item xs={6}>
        <Paper elevation={3}
            sx={{
                height: "205px",
                textAlign: "center",
                overflowY: 'auto',
                padding: "10px"}}>
          <Typography sx={{textAlign: "left", fontSize: 24}}>Grading behaviour</Typography>
         
          <GradeIcon color="primary" sx={{ fontSize: 80, ml: 1}}/>
          <Typography sx={{mr: 0.5, ml: 0.5}}>
            {gradingBehaviour}
          </Typography>
        </Paper>
      </Grid>
      <Grid item xs={6}>
        <Paper elevation={3}
            sx={{
                height: "205px",
                textAlign: "center",
                overflowY: 'auto',
                padding: "10px"}}>
          <Typography  sx={{textAlign: "left", fontSize: 24}}>Assignment type</Typography>
          <QuestionMarkIcon color="primary" sx={{ fontSize: 80, ml: 1}}/>
          <Typography  sx={{ mr: 0.5, ml: 0.5}}>
            {props.assignment.type === 'user' ? 'User' : 'Group'}
          </Typography>
      
        </Paper>
      </Grid>

    </Grid>
    
  );
};
