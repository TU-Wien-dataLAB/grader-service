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
import { IObservableJSON } from '@jupyterlab/observables';

export interface ICommentComponentProps {
  metadata: IObservableJSON;
  gradebook: GradeBook;
  nbname: string;
  nbgraderData: NbgraderData;
  toolData: ToolData;
}

export const CommentComponent = (props: ICommentComponentProps) => {
  const [comment, setComment] = React.useState(
    props.gradebook.getComment(props.nbname, props.toolData.id)
  );

  return (
    <Grid item>
      <TextField
        label="Comment"
        size="small"
        multiline={true}
        value={comment}
        onChange={e => {
          setComment(e.target.value);
          props.metadata.set('updated', true);
          props.gradebook.setComment(
            props.nbname,
            props.toolData.id,
            e.target.value
          );
        }}
      />
    </Grid>
  );
};
