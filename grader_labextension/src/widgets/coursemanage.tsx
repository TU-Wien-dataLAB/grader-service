// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import * as React from 'react';
import { ReactWidget } from '@jupyterlab/apputils';
import { SnackbarProvider } from 'notistack';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { getRoutes } from '../components/coursemanage/routes';
import { Box, Typography, AppBar } from '@mui/material';
import { loadString } from '../services/storage.service';
import { Router } from '@remix-run/router';
import { DialogProvider } from '../components/util/dialog-provider';

export class CourseManageView extends ReactWidget {
  /**
   * Construct a new grading widget
   */
  root: HTMLElement;
  router: Router;

  constructor(options: CourseManageView.IOptions = {}) {
    super();
    this.id = options.id;
    this.addClass('GradingWidget');
    this.root = this.node;

    const savedPath = loadString('course-manage-react-router-path');
    let path = '/';
    if (savedPath !== null && savedPath !== '') {
      console.log(`Restoring path: ${savedPath}`);
      path = savedPath;
    }
    this.router = createMemoryRouter(getRoutes(), { initialEntries: [path] });
  }

  render() {
    return (
      <SnackbarProvider maxSnack={3}>
        <DialogProvider>
          <RouterProvider router={this.router} />
        </DialogProvider>
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
