// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import * as React from 'react';
import { NbgraderData, ToolData } from '../../model';
import { GradeBook } from '../../../../services/gradebook';
import { ExtraCreditComponent, PointsComponent } from './points-component';
import { CommentComponent } from './comment-component';
import { Notebook } from '@jupyterlab/notebook';

export interface GradeComponentProps {
  notebook: Notebook;
  gradebook: GradeBook;
  nbname: string;
  nbgraderData: NbgraderData;
  toolData: ToolData;
}

export const GradeComponent = (props: GradeComponentProps) => {
  const model = props.notebook.model;
  if (model.getMetadata('updated') != undefined) {
    model.setMetadata('updated', false);
  }
  const gradableCell =
    props.toolData.type !== 'readonly' &&
    props.toolData.type !== 'solution' &&
    props.toolData.type !== '';
  const showCommment =
    props.toolData.type === 'task' ||
    props.toolData.type === 'manual' ||
    props.toolData.type === 'solution';

  return (
    <div style={{ marginLeft: '72px' }}>
      {props.toolData.type !== 'readonly' && props.toolData.type !== '' && (
        <div style={{ marginTop: 2, marginBottom: 1 }}>
          {showCommment && (
            <CommentComponent
              model={model}
              nbgraderData={props.nbgraderData}
              toolData={props.toolData}
              gradebook={props.gradebook}
              nbname={props.nbname}
            />
          )}

          {gradableCell && (
            <PointsComponent
              model={model}
              nbgraderData={props.nbgraderData}
              toolData={props.toolData}
              gradebook={props.gradebook}
              nbname={props.nbname}
            />
          )}

          {gradableCell && (
            <ExtraCreditComponent
              model={model}
              nbgraderData={props.nbgraderData}
              toolData={props.toolData}
              gradebook={props.gradebook}
              nbname={props.nbname}
            />
          )}
          <hr style={{ borderTop: '1px', color: 'lightgray' }} />
        </div>
      )}
    </div>
  );
};
