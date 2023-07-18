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
    const router = createMemoryRouter(getRoutes(this.root));
    return (
      <SnackbarProvider maxSnack={3}>
        <Box>
          <Typography variant={'h4'} sx={{ flexGrow: 1, mt: 1.25}} align={'center'} component={'div'}>Course Management</Typography>
        </Box>
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
