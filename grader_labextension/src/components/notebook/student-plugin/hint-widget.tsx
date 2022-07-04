// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import { ReactWidget } from '@jupyterlab/apputils';
import * as React from 'react';

import { HintComponent } from './hint-component';

export class HintWidget extends ReactWidget {
  private readonly hint: string;
  private showAlert = true;

  constructor(hint: string) {
    super();
    this.hint = hint;
  }

  public toggleShowAlert() {
    this.showAlert = !this.showAlert;
  }

  protected render(): any {
    return <HintComponent hint={this.hint} show={this.showAlert} />;
  }
}
