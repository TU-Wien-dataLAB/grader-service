// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import { GlobalObjects } from '../../../index';
import { MainAreaWidget } from '@jupyterlab/apputils';
import { ITerminal } from '@jupyterlab/terminal';
import { Terminal } from '@jupyterlab/services';
import { enqueueSnackbar } from 'notistack';

let terminalSession: Terminal.ITerminalConnection = null;

export const openTerminal = async (path: string) => {
  console.log('Opening terminal at: ' + path.replace(' ', '\\ '));
  let args = {};
  if (
    terminalSession !== null &&
    terminalSession.connectionStatus === 'connected'
  ) {
    args = { name: terminalSession.name };
  }
  const main = (await GlobalObjects.commands.execute(
    'terminal:open',
    args
  )) as MainAreaWidget<ITerminal.ITerminal>;

  if (main) {
    const terminal = main.content;
    terminalSession = terminal.session;
  }

  try {
    terminalSession.send({
      type: 'stdin',
      content: ['cd ' + path.replace(' ', '\\ ') + '\n']
    });
  } catch (e) {
    enqueueSnackbar('Error Opening Terminal', {
      variant: 'error'
    });
    main.dispose();
  }
};

export const openBrowser = async (path: string) => {
  GlobalObjects.commands
    .execute('filebrowser:go-to-path', {
      path
    })
    .catch(e => {
      enqueueSnackbar(e.message, {
        variant: 'error'
      });
    });
};
