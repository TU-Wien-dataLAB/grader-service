// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import * as React from 'react';
import { NbgraderData, ToolData } from '../../model';
import { GradeBook } from '../../../../services/gradebook';
import { INotebookModel } from '@jupyterlab/notebook';

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

  return (
    <span style={{ marginRight: '16px' }}>
      Points:
      <input
        style={{ marginLeft: '4px' }}
        type="number"
        value={points}
        max={props.toolData.points}
        min={0}
        step={0.25}
        onChange={e => {
          setPoints(parseFloat(e.target.value));
          props.model.setMetadata('updated', true);
          props.gradebook.setManualScore(
            props.nbname,
            props.toolData.id,
            parseFloat(e.target.value)
          );
        }}
      />
    </span>
  );
};

export const ExtraCreditComponent = (props: IPointsComponentProps) => {
  const [extraCredit, setExtraCredit] = React.useState(
    props.gradebook.getExtraCredit(props.nbname, props.toolData.id)
  );

  return (
    <span style={{ marginRight: '16px' }}>
      Extra Credit:
      <input
        style={{ marginLeft: '4px' }}
        type="number"
        value={extraCredit}
        max={10000}
        min={0}
        step={0.25}
        onChange={e => {
          setExtraCredit(parseFloat(e.target.value));
          props.model.setMetadata('updated', true);
          props.gradebook.setExtraCredit(
            props.nbname,
            props.toolData.id,
            parseFloat(e.target.value)
          );
        }}
      />
    </span>
  );
};
