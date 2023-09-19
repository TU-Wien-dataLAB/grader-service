// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import * as React from 'react';
import { ReactWidget } from '@jupyterlab/apputils';
import { SnackbarProvider } from 'notistack';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { getRoutes } from '../components/assignment/routes';
import { loadString } from '../services/storage.service';
import { Router } from '@remix-run/router';
import { DialogProvider } from '../components/util/dialog-provider';

export class AssignmentManageView extends ReactWidget {
  /**
   * Construct a new assignment list widget
   */
  router: Router;

  constructor(options: AssignmentManageView.IOptions = {}) {
    super();
    this.id = options.id;
    this.addClass('GradingWidget');

    const savedPath = loadString('assignment-manage-react-router-path');
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
