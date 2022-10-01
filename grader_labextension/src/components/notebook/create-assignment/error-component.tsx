// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import { Notebook } from '@jupyterlab/notebook';
import { Button } from '@blueprintjs/core';
import { Cell } from '@jupyterlab/cells';
import * as React from 'react';

import { Alert } from '@mui/material';

export interface IErrorComponentProps {
  err: string;
}

export const ErrorComponent = (props: IErrorComponentProps) => {
  //const alertStyle = { width: 250 };

  return (
    <Alert sx={{ mt: 1 }} variant="filled" severity="error">
      {props.err}
    </Alert>
  );
};
