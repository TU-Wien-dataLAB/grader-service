// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import {Cell} from '@jupyterlab/cells';
import {Notebook, NotebookPanel} from '@jupyterlab/notebook';
import {PanelLayout} from '@lumino/widgets';
import React from 'react';
import {IModeSwitchProps} from '../slider';
import {CreationWidget} from './creation-widget';
import {ErrorWidget} from './error-widget';
import {Stack, styled, Switch, Typography} from "@mui/material";
import {Validator} from "./validator";

export const AntSwitch = styled(Switch)(({ theme }) => ({
  width: 28,
  height: 16,
  padding: 0,
  display: 'flex',
  '&:active': {
    '& .MuiSwitch-thumb': {
      width: 15,
    },
    '& .MuiSwitch-switchBase.Mui-checked': {
      transform: 'translateX(9px)',
    },
  },
  '& .MuiSwitch-switchBase': {
    padding: 2,
    '&.Mui-checked': {
      transform: 'translateX(12px)',
      color: '#fff',
      '& + .MuiSwitch-track': {
        opacity: 1,
        backgroundColor: theme.palette.mode === 'dark' ? '#177ddc' : '#1890ff',
      },
    },
  },
  '& .MuiSwitch-thumb': {
    boxShadow: '0 2px 4px 0 rgb(0 35 11 / 20%)',
    width: 12,
    height: 12,
    borderRadius: 6,
    transition: theme.transitions.create(['width'], {
      duration: 200,
    }),
  },
  '& .MuiSwitch-track': {
    borderRadius: 16 / 2,
    opacity: 1,
    backgroundColor:
      theme.palette.mode === 'dark' ? 'rgba(255,255,255,.35)' : 'rgba(0,0,0,.25)',
    boxSizing: 'border-box',
  },
}));

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
    this.setState({mode: !this.state.mode}, () => {
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
        <Stack direction="row" spacing={1}  alignItems={"center"} >
        <AntSwitch checked={this.state.mode} onChange={this.handleChange}/>
        <Typography variant="caption" >Creation Mode</Typography>
        <Validator notebook={this.notebook}/>
      </Stack>
    );
  }
}
