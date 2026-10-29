// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import { Cell } from '@jupyterlab/cells';
import { Notebook } from '@jupyterlab/notebook';
import { PanelLayout } from '@lumino/widgets';
import React from 'react';
import { IModeSwitchProps } from '../slider';
import { CreationWidget } from './creation-widget';
import { ErrorWidget } from './error-widget';
import { Switch } from '../../../shadcn-components/ui/switch';
import { Validator } from './validator';

export class CreationModeSwitch extends React.Component<IModeSwitchProps> {
  public state = {
    mode: false
  };
  private notebook: Notebook;

  private onChange: any;

  public constructor(props: IModeSwitchProps) {
    super(props);
    this.state.mode = props.mode || false;
    this.notebook = props.notebook;
    this.onChange = this.props.onChange;
  }

  protected handleChange = async () => {
    this.setState({ mode: !this.state.mode }, () => {
      this.onChange(this.state.mode);
      this.notebook.widgets.map((c: Cell) => {
        const currentLayout = c.layout as PanelLayout;
        if (this.state.mode) {
          currentLayout.insertWidget(0, new CreationWidget(c));
        } else {
          currentLayout.widgets.map(w => {
            if (w instanceof CreationWidget || w instanceof ErrorWidget) {
              try {
                currentLayout.removeWidget(w);
              } catch (error: any) {
                console.log('Could not remove widget of cell: ' + w.cell.id);
                console.log('Error: ' + error);
              }
            }
          });
        }
      });
    });
  };

  public render() {
    return (
      <div className="flex flex-row items-center gap-2">
        <Switch checked={this.state.mode} onCheckedChange={this.handleChange} />
        <span className="text-sm">Creation Mode</span>
        <Validator notebook={this.notebook} />
      </div>
    );
  }
}
