// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import * as React from 'react';
import {Cell} from '@jupyterlab/cells';
import {CellModel, CellType} from '../model';
import {
  Alert,
  Box,
  Divider,
  Grid,
  MenuItem, styled, Switch,
  TextField
} from '@mui/material';

export const AntSwitch = styled(Switch)(({theme}) => ({
  width: 28,
  height: 16,
  padding: 0,
  display: 'flex',
  '&:active': {
    '& .MuiSwitch-thumb': {
      width: 15
    },
    '& .MuiSwitch-switchBase.Mui-checked': {
      transform: 'translateX(9px)'
    }
  },
  '& .MuiSwitch-switchBase': {
    padding: 2,
    '&.Mui-checked': {
      transform: 'translateX(12px)',
      color: '#fff',
      '& + .MuiSwitch-track': {
        opacity: 1,
        backgroundColor: theme.palette.mode === 'dark' ? '#177ddc' : '#1890ff'
      }
    }
  },
  '& .MuiSwitch-thumb': {
    boxShadow: '0 2px 4px 0 rgb(0 35 11 / 20%)',
    width: 12,
    height: 12,
    borderRadius: 6,
    transition: theme.transitions.create(['width'], {
      duration: 200
    })
  },
  '& .MuiSwitch-track': {
    borderRadius: 16 / 2,
    opacity: 1,
    backgroundColor:
      theme.palette.mode === 'dark'
        ? 'rgba(255,255,255,.35)'
        : 'rgba(0,0,0,.25)',
    boxSizing: 'border-box'
  }
}));


export interface ICreationComponentProps {
  cell: Cell;
}

const randomString = (length: number) => {
  let result = '';
  const chars = 'abcdef0123456789';
  let i;
  for (i = 0; i < length; i++) {
    result += chars[Math.floor(Math.random() * chars.length)];
  }
  return result;
};

export const CreationComponent = (props: ICreationComponentProps) => {
  const nbgraderData = CellModel.getNbgraderData(props.cell.model.metadata);
  const toolData = CellModel.newToolData(nbgraderData, props.cell.model.type);
  const [type, setType] = React.useState(toolData.type);
  const [id, setId] = React.useState(toolData.id);
  const [points, setPoints] = React.useState(toolData.points);
  const [hintChecked, setChecked] = React.useState(
    props.cell.model.metadata.has('hint')
  );
  const [hint, setHint] = React.useState(
    hintChecked ? props.cell.model.metadata.get('hint') : ''
  );

  const handleHintChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setChecked(event.target.checked);
  };
  const updateMetadata = () => {
    toolData.type = type as CellType;
    if (id === undefined) {
      setId('cell-' + randomString(16));
    } else {
      toolData.id = id;
    }
    toolData.points = points;
    const data = CellModel.newNbgraderData(toolData);
    CellModel.setNbgraderData(data, props.cell.model.metadata);
    //TODO: Currently we set the optional hint differently than the grader data, but maybe we should do it like this
    if (hintChecked) {
      props.cell.model.metadata.set('hint', hint);
    } else {
      props.cell.model.metadata.delete('hint');
    }
  };

  React.useEffect(() => {
    updateMetadata();
  });

  const alertStyle = {width: 250};
  const gradableCell =
    type !== ('readonly' as CellType) &&
    type !== ('solution' as CellType) &&
    type !== '';
  const solutionCell = type === 'solution' || type === 'manual';

  return (
    <Box>
      <Divider/>
      <Box sx={{mt: 2, mb: 1, ml: 3}}>
        <Grid container spacing={1}>
          <Grid item>
            <TextField
              label="Type"
              select
              size="small"
              sx={{minWidth: 150}}
              value={type}
              onChange={e => {
                setType(e.target.value as CellType);
              }}
            >
              <MenuItem value="">-</MenuItem>
              <MenuItem value="readonly">Readonly</MenuItem>
              {props.cell.model.type === 'code' && (
                <MenuItem value="solution">Autograded answer</MenuItem>
              )}
              {props.cell.model.type === 'code' && (
                <MenuItem value="tests">Autograded tests</MenuItem>
              )}
              <MenuItem value="manual">Manual graded answer</MenuItem>
              {props.cell.model.type === 'markdown' && (
                <MenuItem value="task">Manual graded task</MenuItem>
              )}
            </TextField>
          </Grid>

          {type !== '' && (
            <Grid item>
              <TextField
                size="small"
                label="ID"
                value={id}
                onChange={e => setId(e.target.value)}
                error={id === ''}
                helperText={id === '' ? 'ID not set' : ' '}
              ></TextField>
            </Grid>
          )}

          {gradableCell && (
            <Grid item>
              <TextField
                size="small"
                label="Points"
                value={points}
                type="number"
                onChange={e => setPoints(parseFloat(e.target.value))}
                InputProps={{
                  inputProps: {
                    max: 10000,
                    min: 0,
                    step: 0.25
                  }
                }}
                error={points === undefined}
                helperText={points === undefined ? 'Points not set' : ' '}
              />
            </Grid>
          )}

          {solutionCell && (
            <Grid item>
              <AntSwitch
                sx={{ mt: 2, ml: 1 }}
                checked={hintChecked}
                onChange={handleHintChange}
                inputProps={{'aria-label': 'controlled'}}
              />
            </Grid>
          )}
          {solutionCell && (
            <Grid item>
              <TextField
                size="small"
                label="Optional hint"
                value={hint}
                disabled={!hintChecked}
                onChange={e => setHint(e.target.value)}
              ></TextField>
            </Grid>
          )}

          {type === '' && (
            <Grid item>
              <Alert variant="outlined" sx={alertStyle} severity="warning">
                Type not set
              </Alert>
            </Grid>
          )}

          {points === 0 && (
            <Grid item>
              <Alert variant="outlined" sx={alertStyle} severity="warning">
                Gradable cell with zero points
              </Alert>
            </Grid>
          )}
        </Grid>
      </Box>
    </Box>
  );
};
