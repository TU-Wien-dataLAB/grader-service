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
import { GlobalObjects } from '../../../../index';
import CssBaseline from '@mui/material/CssBaseline';
import { ThemeProvider } from '@mui/system';

export interface IPointsComponentProps {
  model: INotebookModel;
  gradebook: GradeBook;
  nbname: string;
  nbgraderData: NbgraderData;
  toolData: ToolData;
}

export const PointsComponent = (props: IPointsComponentProps) => {
  const [points, setPoints] = React.useState(
    props.gradebook.getGradeScore(props.nbname, props.toolData.id)
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
      <CssBaseline />
      <Grid item>
        <TextField
          size='small'
          label='Points'
          type='number'
          value={points}
          onChange={e => {
            setPoints(parseFloat(e.target.value));
            props.model.setMetadata('updated', true);
            props.gradebook.setManualScore(
              props.nbname,
              props.toolData.id,
              parseFloat(e.target.value)
            );
          }}
          InputProps={{
            inputProps: {
              max: props.toolData.points,
              min: 0,
              step: 0.25
            }
          }}
        />
      </Grid>
    </ThemeProvider>
  );
};

export const ExtraCreditComponent = (props: IPointsComponentProps) => {
  const [extraCredit, setExtraCredit] = React.useState(
    props.gradebook.getExtraCredit(props.nbname, props.toolData.id)
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
      <CssBaseline />
      <Grid item>
        <TextField
          size='small'
          label='Extra Credit'
          type='number'
          value={extraCredit}
          onChange={e => {
            setExtraCredit(parseFloat(e.target.value));
            props.model.setMetadata('updated', true);
            props.gradebook.setExtraCredit(
              props.nbname,
              props.toolData.id,
              parseFloat(e.target.value)
            );
          }}
          InputProps={{
            inputProps: {
              max: 10000,
              min: 0,
              step: 0.25
            }
          }}
        />
      </Grid>
    </ThemeProvider>
  );
};
