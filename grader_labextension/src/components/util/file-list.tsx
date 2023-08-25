// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import * as React from 'react';
import {
  Card,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Paper,
  Typography
} from '@mui/material';
import InsertDriveFileRoundedIcon from '@mui/icons-material/InsertDriveFileRounded';
import { GlobalObjects } from '../../index';
import { Contents } from '@jupyterlab/services';
import IModel = Contents.IModel;
import { SxProps } from '@mui/system';
import { Theme } from '@mui/material/styles';
import { getFiles, openFile } from '../../services/file.service';
import { enqueueSnackbar } from 'notistack';
import { grey } from '@mui/material/colors';

interface IFileListProps {
  path: string;
  sx?: SxProps<Theme>;
}

export const FilesList = (props: IFileListProps) => {
  const [files, setFiles] = React.useState([]);

  React.useEffect(() => {
    getFiles(props.path).then(files => setFiles(files));
  }, [props]);

  // generateItems will be fed using the IIterator from the FilterFileBrowserModel
  const generateItems = (files: {value: IModel, done: boolean}[]) => {
    return files.map(file => (
      <ListItem disablePadding >
        <ListItemButton onClick={() => openFile(file.value.path)} dense={true}>
          <ListItemIcon>
            <InsertDriveFileRoundedIcon />
          </ListItemIcon>
          <ListItemText primary={file.value.name} />
        </ListItemButton>
      </ListItem>
    ));
  };

  return (
    <Paper elevation={0} sx={props.sx}>
      <Card sx={{ mt: 1, maxHeight: 200, overflow: 'auto'}} variant="outlined">
        {files.length === 0 ? (
          <Typography variant={'body1'} color={grey[500]} sx={{ ml: 1 }}>
            No Files Found
          </Typography>
        ) : (
          <List dense={false}>{generateItems(files)}</List>
        )}
      </Card>
    </Paper>
  );
};
