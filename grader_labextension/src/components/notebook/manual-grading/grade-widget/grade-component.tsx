// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import * as React from 'react';
import { Cell } from '@jupyterlab/cells';
import { Box, Divider, Grid, TextField, Typography } from '@mui/material';
import { CellModel, NbgraderData, ToolData } from '../../model';
import { GradeBook } from '../../../../services/gradebook';
import { ExtraCreditComponent, PointsComponent } from './points-component';
import { CommentComponent } from './comment-component';
import { Notebook } from '@jupyterlab/notebook';

export interface GradeComponentProps {
  notebook: Notebook;
  gradebook: GradeBook;
  nbname: string;
  nbgraderData: NbgraderData;
  toolData: ToolData;
}

export const GradeComponent = (props: GradeComponentProps) => {
  const metadata = props.notebook.model.metadata;
  if (!metadata.has('updated')) {
    metadata.set('updated', false);
  }
  const gradableCell =
    props.toolData.type !== 'readonly' &&
    props.toolData.type !== 'solution' &&
    props.toolData.type !== '';
  const showCommment =
    props.toolData.type === 'task' ||
    props.toolData.type === 'manual' ||
    props.toolData.type === 'solution';

  return (
    <Box>
      {props.toolData.type !== 'readonly' && props.toolData.type !== '' && (
        <Box sx={{ mt: 2, mb: 1, ml: 5 }}>
          <Grid container spacing={2}>
            {showCommment && (
              <CommentComponent
                metadata={metadata}
                nbgraderData={props.nbgraderData}
                toolData={props.toolData}
                gradebook={props.gradebook}
                nbname={props.nbname}
              />
            )}

            {gradableCell && (
              <PointsComponent
                metadata={metadata}
                nbgraderData={props.nbgraderData}
                toolData={props.toolData}
                gradebook={props.gradebook}
                nbname={props.nbname}
              />
            )}

            {gradableCell && (
              <ExtraCreditComponent
                metadata={metadata}
                nbgraderData={props.nbgraderData}
                toolData={props.toolData}
                gradebook={props.gradebook}
                nbname={props.nbname}
              />
            )}
          </Grid>
        </Box>
      )}
    </Box>
  );
};
