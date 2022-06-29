// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import { ReactWidget } from '@jupyterlab/apputils';
import * as React from 'react';

import { HintCompontent } from './hint-component';

export class HintWidget extends ReactWidget {
  public hint: string;

  constructor(hint: string) {
    super();
    this.hint = hint;
  }

  protected render(): any {
    return <HintCompontent hint={this.hint} />;
  }
}
