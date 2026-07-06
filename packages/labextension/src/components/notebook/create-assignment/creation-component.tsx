// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import * as React from 'react';
import { Cell } from '@jupyterlab/cells';
import { CellModel, CellType } from '../model';
import { Alert } from '@mui/material';

export interface ICreationComponentProps {
  cell: Cell;
}

const randomString = (length: number) => {
  let result = '';
  const chars = 'abcdef0123456789';
  for (let i = 0; i < length; i++) {
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
    props.cell.model.getMetadata('hint') != null
  );
  const [hint, setHint] = React.useState(
    hintChecked ? props.cell.model.getMetadata('hint') : ''
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
    if (data === null) {
      CellModel.deleteNbgraderData(props.cell.model);
    } else {
      CellModel.setNbgraderData(data, props.cell.model);
    }
    //TODO: Currently we set the optional hint differently than the grader data, but maybe we should do it like this
    if (hintChecked) {
      props.cell.model.setMetadata('hint', hint);
    } else {
      props.cell.model.deleteMetadata('hint');
    }
  };

  React.useEffect(() => {
    updateMetadata();
  });

  const alertStyle = { width: '100%', mt: 2 };
  const gradableCell =
    type !== ('readonly' as CellType) &&
    type !== ('solution' as CellType) &&
    type !== '';
  const solutionCell = type === 'solution' || type === 'manual';

  return (
    <div
      className={'creation-container'}
      style={{ marginTop: '16px', marginBottom: '8px', marginLeft: '24px' }}
    >
      <style>{`
        input:invalid { border: 1px solid red; border-radius: 2px; background: rgba(255,0,0,0.2); }
        .creation-container > span > * { margin-right: 16px; }
      `}</style>
      <span>
        <select
          style={{ minWidth: 150 }}
          value={type}
          onChange={e => {
            setType(e.target.value as CellType);
          }}
        >
          <option value="">-</option>
          <option value="readonly">Readonly</option>
          {props.cell.model.type === 'code' && (
            <option value="solution">Autograded answer</option>
          )}
          {props.cell.model.type === 'code' && (
            <option value="tests">Autograded tests</option>
          )}
          <option value="manual">Manual graded answer</option>
          {props.cell.model.type === 'markdown' && (
            <option value="task">Manual graded task</option>
          )}
        </select>
      </span>

      {type !== '' && (
        <span>
          <input
            placeholder="ID"
            type={'text'}
            value={id}
            onChange={e => setId(e.target.value)}
            required
            // onInput={(event) => {
            //   const input = event.currentTarget;
            //   input.setCustomValidity(input.value === '' ? 'Cell ID is required' : '');
            //   input.reportValidity();
            // }}
          ></input>
        </span>
      )}

      {gradableCell && (
        <span>
          Points:
          <input
            placeholder="Points"
            value={points}
            type="number"
            max={10000}
            min={0}
            step={0.25}
            onChange={e => setPoints(parseFloat(e.target.value))}
            required
          />
        </span>
      )}

      {solutionCell && (
        <span>
          <input
            type={'checkbox'}
            style={{ marginTop: '16px', marginLeft: '8px' }}
            checked={hintChecked}
            onChange={handleHintChange}
            aria-label={'controlled'}
          />
        </span>
      )}
      {solutionCell && (
        <span>
          <input
            placeholder="Optional hint"
            value={hint}
            disabled={!hintChecked}
            onChange={e => setHint(e.target.value)}
          ></input>
        </span>
      )}

      {type === '' && (
        <span>
          <Alert variant="outlined" sx={alertStyle} severity="warning">
            Type not set
          </Alert>
        </span>
      )}

      {points === 0 && (
        <span>
          <Alert variant="outlined" sx={alertStyle} severity="warning">
            Gradable cell with zero points
          </Alert>
        </span>
      )}
    </div>
  );
};
