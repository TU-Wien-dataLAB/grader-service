// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import * as React from 'react';

export interface IErrorComponentProps {
  err: string;
}

export const ErrorComponent = (props: IErrorComponentProps) => {
  return (
    <div className="mt-1 rounded-md border border-destructive/50 bg-destructive/10 px-4 py-3 text-sm text-destructive">
      {props.err}
    </div>
  );
};
