// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import * as React from 'react';
import { ReactWidget } from '@jupyterlab/apputils';
import { LectureListComponent } from '../components/assignment/lecture-list';
import { SnackbarProvider } from 'notistack';

export class AssignmentList extends ReactWidget {
  /**
   * Construct a new assignment list widget
   */
  constructor(options: AssignmentList.IOptions = {}) {
    super();
    this.id = options.id;
    this.addClass('GradingWidget');
  }

  render(): JSX.Element {
    const root = this.node;
    return (
      <SnackbarProvider maxSnack={3}>
        <LectureListComponent root={root} />
      </SnackbarProvider>
    );
  }
}

export namespace AssignmentList {
  /**
   * An options object for initializing a assignment list view widget.
   */
  export interface IOptions {
    /**
     * The widget/DOM id of the assignment list view.
     */
    id?: string;
  }
}
