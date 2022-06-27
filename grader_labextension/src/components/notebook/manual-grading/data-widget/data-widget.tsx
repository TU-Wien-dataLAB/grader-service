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
import { DataComponent } from './data-component';

export class DataWidget extends ReactWidget {
  public cell: Cell;
  public gradebook: GradeBook;
  public nbname: string;

  constructor(cell: Cell, gradebook: GradeBook, nbname: string) {
    super();
    this.cell = cell;
    this.gradebook = gradebook;
    this.nbname = nbname;
  }

  protected render():
    | ReactElement<any, string | JSXElementConstructor<any>>[]
    | ReactElement<any, string | JSXElementConstructor<any>> {
    return (
      <DataComponent
        cell={this.cell}
        gradebook={this.gradebook}
        nbname={this.nbname}
      />
    );
  }
}
