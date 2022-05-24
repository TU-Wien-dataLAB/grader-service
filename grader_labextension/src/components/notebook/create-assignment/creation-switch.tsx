// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import { Button, Switch } from '@blueprintjs/core';
import { Cell } from '@jupyterlab/cells';
import { Notebook, NotebookPanel } from '@jupyterlab/notebook';
import { PanelLayout } from '@lumino/widgets';
import React from 'react';
import { Assignment } from '../../../model/assignment';
import { Lecture } from '../../../model/lecture';
import { GradeBook } from '../../../services/gradebook';
import { NbgraderData } from '../model';
import { IModeSwitchProps } from '../slider';
import { CellWidget } from './cellwidget';
import { CreationWidget } from './creation-widget';
import { ErrorWidget } from './error-widget';
import { CellPlayButton } from './widget';

export class CreationModeSwitch extends React.Component<IModeSwitchProps> {
  public state = {
    mode: false
  };
  private notebook: Notebook;
  private notebookpanel: NotebookPanel;

  private onChange: any;

  public constructor(props: IModeSwitchProps) {
    super(props);
    this.state.mode = props.mode || false;
    this.notebook = props.notebook;
    this.notebookpanel = props.notebookpanel;
    this.onChange = this.props.onChange;
  }

  protected handleChange = async () => {
    this.setState({ mode: !this.state.mode }, () => {
      const ids = new Set();
      this.onChange(this.state.mode);
      this.notebook.widgets.map((c: Cell) => {
        const currentLayout = c.layout as PanelLayout;
        if (this.state.mode) {
          currentLayout.insertWidget(0, new CreationWidget(c));
        } else {
          currentLayout.widgets.map(w => {
            if (w instanceof CreationWidget || w instanceof ErrorWidget) {
              currentLayout.removeWidget(w);
            }
          });
        }
      });
    });
  };

  public render() {
    return (
      <Switch
        checked={this.state.mode}
        label="Creationmode"
        onChange={this.handleChange}
      />
    );
  }
}
