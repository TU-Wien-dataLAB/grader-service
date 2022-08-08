// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import { Notebook } from '@jupyterlab/notebook';
import { Button } from '@blueprintjs/core';
import { Cell } from '@jupyterlab/cells';
import * as React from 'react';
import { CellModel, NbgraderData, ToolData } from '../model';
import { PanelLayout, Widget } from '@lumino/widgets';
import { ErrorWidget } from './error-widget';
import {
  Button as MuiButton,
  Alert,
  AlertTitle,
  Box,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Stack
} from '@mui/material';

export interface ValidatorProps {
  notebook: Notebook;
}

export interface ReportItem {
  id: string;
  type: 'error' | 'warning';
  msg: string;
}

export const Validator = (props: ValidatorProps) => {
  const [dialogOpen, setDialog] = React.useState(false);
  const [results, setResult] = React.useState([]);
  const validateNotebook = () => {
    //check duplicate ids
    const ids = new Set();
    const result: ReportItem[] = [];
    console.log('started validation');
    props.notebook.widgets.map((c: Cell) => {
      (c.layout as PanelLayout).widgets.map((w: Widget) => {
        if (w instanceof ErrorWidget) {
          c.layout.removeWidget(w);
        }
      });
    });
    props.notebook.widgets.map((c: Cell) => {
      const metadata: NbgraderData = CellModel.getNbgraderData(
        c.model.metadata
      );
      const toolData: ToolData = CellModel.newToolData(metadata, c.model.type);
      if (metadata !== null) {
        if (metadata.grade_id !== null) {
          if (ids.has(metadata.grade_id)) {
            console.log('duplicate id found');
            const layout = c.layout as PanelLayout;
            layout.insertWidget(0, new ErrorWidget(c, 'Duplicate ID found'));
            result.push({
              id: metadata.grade_id,
              type: 'error',
              msg: 'Duplicate ID found'
            });
          } else {
            ids.add(metadata.grade_id);
          }
        }
      } else {
        result.push({
          id: 'Warning',
          type: 'warning',
          msg: 'Cell with no type found'
        });
      }
    });
    setResult(result);
    setDialog(true);
  };

  const handleClose = () => {
    setDialog(false);
  };
  return (
    <Box>
      <Button
        className="jp-ToolbarButtonComponent grader-toolbar-button"
        onClick={validateNotebook}
        icon="automatic-updates"
        minimal
        intent="success"
        small={true}
      >
        Validate
      </Button>
      <Dialog
        open={dialogOpen}
        onClose={handleClose}
        aria-labelledby="alert-dialog-title"
        aria-describedby="alert-dialog-description"
      >
        <DialogTitle id="alert-dialog-title">{'Validation Report'}</DialogTitle>
        <DialogContent>
          <Stack spacing={2}>
            {results.length === 0 && (
              <Box sx={{ width: '450px' }}>
                <Alert severity="success">
                  <AlertTitle>No errors found</AlertTitle>
                </Alert>
              </Box>
            )}
            {results.map((e: ReportItem) => (
              <Box sx={{ width: '450px' }}>
                <Alert severity={e.type}>
                  <AlertTitle>{e.id}</AlertTitle>
                  {e.msg}
                </Alert>
              </Box>
            ))}
          </Stack>
        </DialogContent>
        <DialogActions>
          <MuiButton onClick={handleClose} autoFocus>
            Ok
          </MuiButton>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
