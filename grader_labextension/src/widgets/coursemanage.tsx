// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import * as React from 'react';
import { ReactWidget } from '@jupyterlab/apputils';
import { SnackbarProvider } from 'notistack';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { getRoutes } from "../components/coursemanage/routes";
import {Box, Typography, AppBar} from "@mui/material";
import { loadString } from '../services/storage.service';

export class CourseManageView extends ReactWidget {
  /**
   * Construct a new grading widget
   */
  root: HTMLElement;

  constructor(options: CourseManageView.IOptions = {}) {
    super();
    this.id = options.id;
    this.addClass('GradingWidget');
    this.root = this.node;

  }

  render() {
    const savedPath = loadString('course-manage-react-router-path');
    let path = "/"
    if (savedPath !== null && savedPath !== '') {
      console.log(`Restoring path: ${savedPath}`);
      path = savedPath;
    }
    const router = createMemoryRouter(getRoutes(this.root), { initialEntries: [path] });
    return (
      <SnackbarProvider maxSnack={3}>
        <RouterProvider router={router} />
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
