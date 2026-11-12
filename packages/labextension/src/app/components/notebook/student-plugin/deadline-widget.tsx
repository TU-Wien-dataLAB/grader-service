// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import { ReactWidget } from '@jupyterlab/apputils';
import * as React from 'react';
import { DeadlineWrapper } from './deadline-wrapper';

export class DeadlineWidget extends ReactWidget {
  private notebookPaths: string[];

  constructor(path: string) {
    super();
    this.notebookPaths = path.split('/');
  }

  protected render(): any {
    return <DeadlineWrapper notebookPaths={this.notebookPaths} />;
  }
}
