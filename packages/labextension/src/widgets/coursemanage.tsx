// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import * as React from 'react';
import { ReactWidget } from '@jupyterlab/apputils';
import { closeSnackbar, SnackbarProvider } from 'notistack';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { getRoutes } from '../components/coursemanage/routes';
import { Button } from '@mui/material';
import { Router } from '@remix-run/router';
import { DialogProvider } from '../components/util/dialog-provider';
import { GlobalObjects } from '../index';
import { createTheme, ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from './assignmentmanage';
// import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

export class CourseManageView extends ReactWidget {
  /**
   * Construct a new grading widget
   */
  router: Router;
  theme: 'dark' | 'light';

  constructor(options: CourseManageView.IOptions = {}) {
    super();
    this.id = options.id || 'course-manage-view';
    this.addClass('GradingWidget');
    this.router = createMemoryRouter(getRoutes(), { initialEntries: ['/'] });

    const themeManager = GlobalObjects.themeManager;
    this.theme = themeManager.isLight(themeManager.theme ?? 'light')
      ? 'light'
      : 'dark';

    themeManager.themeChanged.connect(() => {
      this.theme = themeManager.isLight(themeManager.theme ?? 'light')
        ? 'light'
        : 'dark';
    }, this);
  }

  render() {
    return (
      <QueryClientProvider client={queryClient}>
        {/* <ReactQueryDevtools initialIsOpen={false} /> */}
        <ThemeProvider theme={createTheme({ palette: { mode: this.theme } })}>
          <CssBaseline />
          <SnackbarProvider
            maxSnack={3}
            // the parent of the parent is the main dock panel in JupyterLab
            domRoot={this.node.parentNode.parentElement}
            action={snackbarId => (
              <Button
                variant="outlined"
                size="small"
                style={{ color: 'white', borderColor: 'white' }}
                onClick={() => closeSnackbar(snackbarId)}
              >
                Dismiss
              </Button>
            )}
          >
            <DialogProvider>
              <RouterProvider router={this.router} />
            </DialogProvider>
          </SnackbarProvider>
        </ThemeProvider>
      </QueryClientProvider>
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
