// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import * as React from 'react';
import { Cell } from '@jupyterlab/cells';
import { CellModel, CellType } from '../model';
import { Checkbox } from '../../../shadcn-components/ui/checkbox';
import { TriangleAlert } from 'lucide-react';

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
    props.cell.model.getMetadata('hint') !== undefined
  );
  const [hint, setHint] = React.useState(
    hintChecked ? props.cell.model.getMetadata('hint') : ''
  );
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

  const gradableCell =
    type !== ('readonly' as CellType) &&
    type !== ('solution' as CellType) &&
    type !== '';
  const solutionCell = type === 'solution' || type === 'manual';

  return (
    <div className={'mt-4 mb-2 ml-6'}>
      <div id={'creation-container'} className={'flex items-center gap-4'}>
        <style>{`
        input:invalid { border: 1px solid red; border-radius: 2px; background: rgba(255,0,0,0.2); }
      `}</style>
        <span>
          <select
            className={
              'min-w-37.5 border border-border/50 px-1 py-0.5 bg-muted-foreground/10 rounded-xs'
            }
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
              className={
                'min-w-37.5 border border-border/50 px-1 py-0.5 rounded-xs'
              }
              placeholder="ID"
              type={'text'}
              value={id}
              onChange={e => setId(e.target.value)}
              required
            ></input>
          </span>
        )}

        {gradableCell && (
          <span>
            Points:
            <input
              placeholder="Points"
              className={
                'min-w-37.5 border border-border/50 px-1 py-0.5 rounded-xs ml-1'
              }
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
          <span className={'flex items-center'}>
            <Checkbox
              className={'border border-border/50 rounded-xs'}
              checked={hintChecked}
              onCheckedChange={() => setChecked(!hintChecked)}
              aria-label={'controlled'}
            />
          </span>
        )}
        {solutionCell && (
          <span>
            <input
              placeholder="Optional hint"
              className={
                'min-w-37.5 border border-border/50 px-1 py-0.5 rounded-xs'
              }
              value={hint}
              disabled={!hintChecked}
              onChange={e => setHint(e.target.value)}
            ></input>
          </span>
        )}
      </div>
      {type === '' && (
        <span className="block w-full mt-2">
          <div className="rounded-xs gap-2 flex flex-row border items-center border-yellow-500/50 bg-yellow-500/10 px-4 py-3 text-sm text-yellow-700 dark:text-yellow-400">
            <TriangleAlert className={'text-yellow-700'} />
            Type not set
          </div>
        </span>
      )}
      {points === 0 && (
        <span className="block w-full mt-2">
          <div className="rounded-xs gap-2 flex flex-row items-center border border-yellow-500/50 bg-yellow-500/10 px-4 py-3 text-sm text-yellow-700 dark:text-yellow-400">
            <TriangleAlert className={'text-yellow-700'} />
            Gradable cell with zero points
          </div>
        </span>
      )}
    </div>
  );
};
