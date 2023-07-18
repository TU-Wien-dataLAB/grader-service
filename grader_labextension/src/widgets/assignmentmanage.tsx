// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import * as React from 'react';
import { ReactWidget } from '@jupyterlab/apputils';
import { SnackbarProvider } from 'notistack';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { getRoutes } from "../components/assignment/routes";

export class AssignmentManageView extends ReactWidget {
  /**
   * Construct a new assignment list widget
   */
   root: HTMLElement;

  constructor(options: AssignmentManageView.IOptions = {}) {
    super();
    this.id = options.id;
    this.addClass('GradingWidget');
    this.root = this.node;
  }

  render() {
      const router = createMemoryRouter(getRoutes(this.root));
    return (
      <SnackbarProvider maxSnack={3}>
        <RouterProvider router={router} />
      </SnackbarProvider>
    );
  }
}

export namespace AssignmentManageView {
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
