// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import { Box, Typography } from '@mui/material';
import * as React from 'react';

export interface IModalTitle {
  title: string;
  children?: React.ReactNode;
}

export const SectionTitle = (props: IModalTitle) => {
  return (
    <Box sx={{ m: 3, top: 3 }}>
      <Typography display="inline-block" variant="h4">
        {props.title}
      </Typography>
      {props.children}
    </Box>
  );
};
