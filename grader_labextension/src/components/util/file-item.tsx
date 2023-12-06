import React from 'react';
import {
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Tooltip,
  Stack,
  Typography,
} from '@mui/material';
import InsertDriveFileRoundedIcon from '@mui/icons-material/InsertDriveFileRounded';
import WarningIcon from '@mui/icons-material/Warning';
import { Contents } from '@jupyterlab/services';
import IModel = Contents.IModel; 

interface IFileItemProps {
  file: { value: IModel; done: boolean };
  inContained: (file: string) => boolean;
  extraFileHelp: string;
  openFile: (path: string) => void;
  allowFiles?: boolean;
}

const FileItem = ({
  file,
  inContained,
  extraFileHelp,
  openFile,
  allowFiles,
}) => {

  return (
    <ListItem disablePadding>
      <ListItemButton onClick={() => openFile(file.value.path)} dense={true}>
        <ListItemIcon>
          <InsertDriveFileRoundedIcon />
        </ListItemIcon>
        <ListItemText 
          primary={<Typography>{file.value.name}</Typography>}
          secondary={
            <Stack direction={'row'} spacing={2}>
              {!inContained(file.value.name) && !allowFiles && (
                <Tooltip title={extraFileHelp}>
                  <Stack direction={'row'} spacing={2} flex={0}>
                    <WarningIcon color={'warning'} fontSize={'small'} />
                    <Typography sx={{ whiteSpace: 'nowrap', minWidth: 'auto' }}>
                      Extra File
                    </Typography>
                  </Stack>
                </Tooltip>
              )}
            </Stack>
          }
        />
      </ListItemButton>
    </ListItem>
  );
};

export default FileItem;