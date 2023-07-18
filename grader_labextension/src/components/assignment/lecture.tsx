// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import {
  Alert,
  Button,
  Card,
  CardActions,
  CardContent,
  Collapse,
  Grid,
  LinearProgress,
  Typography
} from '@mui/material';
import { red } from '@mui/material/colors';
import * as React from 'react';
import { Assignment } from '../../model/assignment';
import { AssignmentCardComponent } from './assignment-card';
import { AssignmentStatus } from './assignment-status';
import { Lecture } from '../../model/lecture';
import { getAllAssignments } from '../../services/assignments.service';
import { AssignmentComponent } from './assignment';
import { loadBoolean, storeBoolean } from '../../services/storage.service';
import { useNavigation, useRouteLoaderData } from 'react-router-dom';

/**
 * Props for LectureComponent.
 */
interface ILectureComponentProps {
  root: HTMLElement;
}

/**
 * Renders the lecture card which contains it's assignments.
 * @param props Props of the lecture component
 */
export const LectureComponent = (props: ILectureComponentProps) => {
    const { lecture, assignments } = useRouteLoaderData('lecture') as {
        lecture: Lecture,
        assignments: Assignment[], 
    };
    const navigation = useNavigation(); 

    const [lectureState, setLecture] = React.useState(lecture); 
    const [assignmentsState, setAssignments] = React.useState(assignments);

    if (navigation.state === 'loading') {
        return (
            <div>
              <Card>
                <LinearProgress />
                </Card>
            </div>
        );
    }

  /**
   * Toggles collapsable in the card body.
   */
  return (
    <div>
      <Card
        sx={{ backgroundColor: 'background.paper' }}
        className='lecture-card'
      >
        <CardContent sx={{ mb: -1, display: 'flex' }}>
          <Typography variant={'h5'} sx={{ mr: 2 }}>
            <Typography
              color={'text.secondary'}
              sx={{
                display: 'inline-block',
                mr: 0.75,
                fontSize: 16
              }}
            >
              Lecture:
            </Typography>
            {lectureState.name}
            {lectureState.complete ? (
              <Typography
                sx={{
                  display: 'inline-block',
                  ml: 0.75,
                  fontSize: 16,
                  color: red[400]
                }}
              >
                complete
              </Typography>
            ) : null}
          </Typography>
        </CardContent>

        <CardContent>
          <Grid container spacing={2} alignItems='stretch'>
            {assignmentsState.map((el: Assignment) => (
              <Grid
                item
                gridAutoColumns={'1fr'}
                sx={{
                  maxWidth: 225,
                  minWidth: 225,
                  minHeight: '100%',
                  m: 1.5
                }}
              >
                <AssignmentCardComponent
                  lecture={lectureState}
                  assignment={el}
                  root={props.root}
                />
              </Grid>
            ))}
            <Grid
              item
              gridAutoColumns={'1fr'}
              sx={{
                maxWidth: 225,
                minWidth: 225,
                minHeight: 225,
                heigth: '100%',
                m: 1.5
              }}
            >
            </Grid>
          </Grid>
        </CardContent>
      </Card>
      </div>
  );
};
