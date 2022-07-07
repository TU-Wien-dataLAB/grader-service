// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import * as React from 'react';
import { ReactWidget } from '@jupyterlab/apputils';
import { CourseManageComponent } from '../components/coursemanage/coursemanage.component';
import { SnackbarProvider } from 'notistack';

export class CourseManageView extends ReactWidget {
  /**
   * Construct a new grading widget
   */
  constructor(options: CourseManageView.IOptions = {}) {
    super();
    this.id = options.id;
    this.addClass('GradingWidget');
  }

  render() {
    const root = this.node;
    return (
      <SnackbarProvider maxSnack={3}>
        <CourseManageComponent root={root} />
      </SnackbarProvider>
    );
  }
}

export namespace CourseManageView {
  /**
   * An options object for initializing a grading view widget.
   */
  export interface IOptions {
    /**
     * The widget/DOM id of the grading view.
     */
    id?: string;
  }
}
