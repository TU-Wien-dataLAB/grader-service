// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import * as React from 'react';
import {
  Box,
  Card,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Paper, Stack, Tooltip,
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
import WarningIcon from '@mui/icons-material/Warning';
import DangerousIcon from '@mui/icons-material/Dangerous';

interface IFileListProps {
  path: string;
  sx?: SxProps<Theme>;
  shouldContain?: string[];
}

export const FilesList = (props: IFileListProps) => {
  const [files, setFiles] = React.useState([]);

  React.useEffect(() => {
    getFiles(props.path).then(files => setFiles(files));
  }, [props]);

  const inContained = (file: string) => {
    if (props.shouldContain) {
      return props.shouldContain.filter(f => file === f).length > 0;
    }
    return true;
  };

  const extraFileHelp = `This file is not part of the assignment and will be removed when grading! Did you rename a notebook file or added it manually?`;
  const missingFileHelp = `This file should be part of your assignment! Did you delete it?`;

  // generateItems will be fed using the IIterator from the FilterFileBrowserModel
  const generateItems = (files: { value: IModel, done: boolean }[]) => {
    return files.map(file => (
      <ListItem disablePadding>
        <ListItemButton onClick={() => openFile(file.value.path)} dense={true}>
          <ListItemIcon>
            <InsertDriveFileRoundedIcon />
          </ListItemIcon>
          <ListItemText primary={<Typography>{file.value.name}</Typography>}
                        secondary={
                          (!inContained(file.value.name))
                            ? <Stack direction={'row'} spacing={2}>
                              <Tooltip title={extraFileHelp}>
                                <Stack direction={'row'} spacing={2} flex={0}>
                                  <WarningIcon color={'warning'} fontSize={'small'} />
                                  <Typography sx={{ whiteSpace: 'nowrap', minWidth: 'auto' }}>Extra File</Typography>
                                </Stack>
                              </Tooltip>
                            </Stack>
                            : null
                        } />
        </ListItemButton>
      </ListItem>
    ));
  };

  // creates items for files that should be included in the file list if shouldContain is specified
  const generateMissingItems = (files: { value: IModel, done: boolean }[]) => {
    if (props.shouldContain) {
      const fileNames = files.map(file => file.value.name);
      const missingFiles = props.shouldContain.filter(f => !fileNames.includes(f));
      return missingFiles.map(file => (
        <ListItem disablePadding>
          <ListItem>
            <ListItemIcon>
              <InsertDriveFileRoundedIcon color={"disabled"} />
            </ListItemIcon>
            <ListItemText primary={<Typography color={"text.secondary"}>{file}</Typography>}
                          secondary={
                            <Stack direction={'row'} spacing={2}>
                              <Tooltip title={missingFileHelp}>
                                  <Stack direction={'row'} spacing={2} flex={0}>
                                    <DangerousIcon color={'error'} fontSize={'small'} />
                                    <Typography sx={{ whiteSpace: 'nowrap', minWidth: 'auto' }}>File Missing</Typography>
                                  </Stack>
                              </Tooltip>
                            </Stack>
                          } />
          </ListItem>
        </ListItem>
      ));
    } else {
      return [];
    }
  };

  return (
    <Paper elevation={0} sx={props.sx}>
      <Card sx={{ mt: 1, maxHeight: 300, overflow: 'auto' }} variant='outlined'>
        {files.length === 0 ? (
          <Typography variant={'body1'} color={grey[500]} sx={{ ml: 1 }}>
            No Files Found
          </Typography>
        ) : (
          <List dense={false}>{[...generateItems(files), ...generateMissingItems(files)]}</List>
        )}
      </Card>
    </Paper>
  );
};
