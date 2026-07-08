// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import * as React from 'react';
import { Cell } from '@jupyterlab/cells';
import { CellModel } from '../../model';
import { GradeBook } from '../../../../services/gradebook';

export interface IDataComponentProps {
  cell: Cell;
  gradebook: GradeBook;
  nbname: string;
}

export const DataComponent = (props: IDataComponentProps) => {
  const nbgraderData = CellModel.getNbgraderData(props.cell.model.metadata);
  const toolData = CellModel.newToolData(nbgraderData, props.cell.model.type);

  const gradableCell =
    toolData.type !== 'readonly' &&
    toolData.type !== 'solution' &&
    toolData.type !== '';

  return (
    <div style={{ margin: '16px 0px 8px 72px' }}>
      <span style={{ marginRight: '16px' }}>Type: {toolData.type}</span>

      <span style={{ marginRight: '16px' }}>ID: {toolData.id}</span>

      {toolData.type === 'tests' && (
        <span style={{ marginRight: '16px' }}>
          Autograded Points:{' '}
          {props.gradebook.getAutoGradeScore(props.nbname, toolData.id)}
        </span>
      )}

      {gradableCell && (
        <span style={{ marginRight: '16px' }}>
          Max Points: {toolData.points}
        </span>
      )}
    </div>
  );
};
