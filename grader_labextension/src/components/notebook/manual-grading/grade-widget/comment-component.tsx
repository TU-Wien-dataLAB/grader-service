// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import * as React from 'react';
import { createTheme, Grid, TextField } from '@mui/material';
import { NbgraderData, ToolData } from '../../model';
import { GradeBook } from '../../../../services/gradebook';
import { INotebookModel } from '@jupyterlab/notebook';
import CssBaseline from '@mui/material/CssBaseline';
import { GlobalObjects } from '../../../../index';
import { ThemeProvider } from '@mui/system';

export interface ICommentComponentProps {
  model: INotebookModel;
  gradebook: GradeBook;
  nbname: string;
  nbgraderData: NbgraderData;
  toolData: ToolData;
}

export const CommentComponent = (props: ICommentComponentProps) => {
  const [comment, setComment] = React.useState(
    props.gradebook.getComment(props.nbname, props.toolData.id)
  );

  const [theme, setTheme] = React.useState(
    createTheme({
      palette: { mode: (GlobalObjects.themeManager.isLight(GlobalObjects.themeManager.theme)) ? 'light' : 'dark' }
    })
  );

  GlobalObjects.themeManager.themeChanged.connect(() => {
    const palette = (GlobalObjects.themeManager.isLight(GlobalObjects.themeManager.theme)) ? 'light' : 'dark';
    setTheme(createTheme({ palette: { mode: palette } }));
  }, this);

  return (
    <ThemeProvider theme={theme}>
      <Grid item>
        <TextField
          label='Comment'
          size='small'
          multiline={true}
          value={comment}
          onChange={e => {
            setComment(e.target.value);
            props.model.setMetadata('updated', true);
            props.gradebook.setComment(
              props.nbname,
              props.toolData.id,
              e.target.value
            );
          }}
        />
      </Grid>
    </ThemeProvider>
  );
};
