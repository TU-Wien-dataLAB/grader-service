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
import * as React from 'react';
import { Assignment } from '../../model/assignment';
import { Lecture } from '../../model/lecture';
import { getAllAssignments } from '../../services/assignments.service';
import { AssignmentComponent } from './assignment';
import { loadBoolean, storeBoolean } from '../../services/storage.service';

/**
 * Props for LectureComponent.
 */
interface ILectureComponentProps {
  lecture: Lecture;
  root: HTMLElement;
  open?: boolean;
}

/**
 * Renders the lecture card which contains it's assignments.
 * @param props Props of the lecture component
 */
export const LectureComponent = (props: ILectureComponentProps) => {
  const [assignments, setAssignments] = React.useState(null as Assignment[]);
  const [expanded, setExpanded] = React.useState(
    loadBoolean('a-expanded', props.lecture) !== null
      ? loadBoolean('a-expanded', props.lecture)
      : props.open
  );

  React.useEffect(() => {
    getAllAssignments(props.lecture.id).then(response => {
      setAssignments(response);
    });
  }, []);
  /**
   * Toggles collapsable in the card body.
   */
  const handleExpandClick = () => {
    storeBoolean('a-expanded', !expanded, props.lecture);
    setExpanded(!expanded);
  };
  if (assignments === null) {
    return (
      <div>
        <Card>
          <LinearProgress />
        </Card>
      </div>
    );
  }
  return (
    <div>
      <Card
        sx={{ backgroundColor: expanded ? '#fafafa' : 'background.paper' }}
        elevation={expanded ? 0 : 2}
        className="lecture-card"
      >
        <CardContent sx={{ mb: -1, display: 'flex' }}>
          <Typography variant={'h5'} sx={{ mr: 2 }}>
            {props.lecture.name}
          </Typography>
        </CardContent>

        <Collapse in={expanded} timeout="auto" unmountOnExit>
          <CardContent>
            <Grid container spacing={2} alignItems="stretch">
              {assignments.map((el: Assignment) => (
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
                  <AssignmentComponent
                    lecture={props.lecture}
                    assignment={el}
                    root={props.root}
                  />
                </Grid>
              ))}
            </Grid>
            {assignments.length === 0 ? (
                <Alert sx={{ m: 3 }} severity="info">
                  No active assignments
                </Alert>
              ) : null}
          </CardContent>
        </Collapse>
        <CardActions>
          <Button size="small" sx={{ ml: 'auto' }} onClick={handleExpandClick}>
            {(expanded ? 'Hide' : 'Show') + ' Assignments'}
          </Button>
        </CardActions>
      </Card>
    </div>
  );
};
