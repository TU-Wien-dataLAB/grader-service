// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import { ReactWidget } from '@jupyterlab/apputils';
import * as React from 'react';
import { Cell } from '@jupyterlab/cells';

import { ReactElement, JSXElementConstructor } from 'react';
import { GradeBook } from '../../../../services/gradebook';
import { GradeComponent } from './grade-component';
import { CellModel, NbgraderData, ToolData } from '../../model';
import { Notebook } from '@jupyterlab/notebook';

export class GradeWidget extends ReactWidget {
  public cell: Cell;
  public notebook: Notebook;
  public gradebook: GradeBook;
  public nbname: string;
  public nbgraderData: NbgraderData;
  public toolData: ToolData;

  constructor(
    cell: Cell,
    notebook: Notebook,
    gradebook: GradeBook,
    nbname: string
  ) {
    super();
    this.cell = cell;
    this.notebook = notebook;
    this.gradebook = gradebook;
    this.nbname = nbname;
    this.nbgraderData = CellModel.getNbgraderData(this.cell.model.metadata);
    this.toolData = CellModel.newToolData(
      this.nbgraderData,
      this.cell.model.type
    );
  }

  protected render():
    | ReactElement<any, string | JSXElementConstructor<any>>[]
    | ReactElement<any, string | JSXElementConstructor<any>> {
    if (this.toolData.type !== '' && this.toolData.type !== 'readonly') {
      return (
        <GradeComponent
          notebook={this.notebook}
          nbgraderData={this.nbgraderData}
          toolData={this.toolData}
          gradebook={this.gradebook}
          nbname={this.nbname}
        />
      );
    } else {
      return null;
    }
  }
}
