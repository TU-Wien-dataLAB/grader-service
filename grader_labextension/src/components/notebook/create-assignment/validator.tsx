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
    props.notebook.widgets.map((c: Cell) => {
      (c.layout as PanelLayout).widgets.map((w: Widget) => {
        if (w instanceof ErrorWidget) {
          c.layout.removeWidget(w);
        }
      });
    });

    let duplicate = 0;
    let noType = 0;
    let wrongTypeSolution = 0;
    let wrongTypeTest = 0;
    let noEndSolution = 0;
    let noEndTest = 0;

    props.notebook.widgets.map((c: Cell) => {
      const metadata: NbgraderData = CellModel.getNbgraderData(
        c.model.metadata
      );
      const cellText = c.model.value.text;
      const layout = c.layout as PanelLayout;
      const toolData: ToolData = CellModel.newToolData(metadata, c.model.type);
      if (metadata !== null) {
        if (metadata.grade_id !== null) {
          //check if the cell id was already found
          if (ids.has(metadata.grade_id)) {
            layout.addWidget(new ErrorWidget(c, 'Duplicate ID found'));
            duplicate += 1;
          } else {
            ids.add(metadata.grade_id);
          }
        }
      } else {
        noType += 1;
      }

      if (
        /#+\s?BEGIN\sSOLUTION/gim.test(cellText) &&
        /#+\s?END\sSOLUTION/gim.test(cellText) === false
      ) {
        noEndSolution += 1;
        layout.addWidget(new ErrorWidget(c, 'No end solution found'));
      }

      if (
        /#+\s?BEGIN\sHIDDEN\sTESTS/gim.test(cellText) &&
        /#+\s?END\sHIDDEN\sTESTS/gim.test(cellText) === false
      ) {
        noEndTest += 1;
        layout.addWidget(new ErrorWidget(c, 'No end hidden tests found'));
      }
      //check if ### BEGIN/END SOLUTION is placed in a cell with the wrong cell type
      if (toolData.type !== 'solution' && toolData.type !== 'manual') {
        if (/#+\s?[BEGIN|END]{1,}\sSOLUTION/gim.test(cellText)) {
          wrongTypeSolution += 1;
          layout.addWidget(new ErrorWidget(c, 'Solution region must be in solution cell'));
        }
      }
      //check if ### BEGIN/END HIDDEN TESTS is placed wrong
      if (toolData.type !== 'tests') {
        if (/#+\s?[BEGIN|END]{1,}\sHIDDEN\stest/gim.test(cellText)) {
          wrongTypeTest += 1;
          layout.addWidget(new ErrorWidget(c, 'Hidden test region must be in autograded test cell'));
        }
      }
    });

    if (duplicate > 0) {
      result.push({
        id: 'Duplicated ID',
        type: 'error',
        msg: duplicate + 'x Duplicate ID found'
      });
    }

    if (noEndSolution > 0) {
      result.push({
        id: 'No End Solution',
        type: 'error',
        msg: noEndSolution + 'x No end solution found'
      });
    }

    if (noEndTest > 0) {
      result.push({
        id: 'No End Tests',
        type: 'error',
        msg: noEndTest + 'x No end hidden tests found'
      });
    }

    if (wrongTypeSolution > 0) {
      result.push({
        id: 'Wrong Solution Region Placement',
        type: 'error',
        msg:
          wrongTypeSolution +
          'x Solution regions can only be placed in solution cells'
      });
    }

    if (wrongTypeTest > 0) {
      result.push({
        id: 'Wrong Test Region Placement',
        type: 'error',
        msg:
          wrongTypeTest +
          'x Hidden test regions can only be placed in autograded test cells'
      });
    }

    if (noType > 0) {
      result.push({
        id: 'No Type Cell',
        type: 'warning',
        msg: noType + 'x Cell with no type found'
      });
    }
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
