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
import KeyboardArrowRightIcon from '@mui/icons-material/KeyboardArrowRight';
import { Contents } from '@jupyterlab/services';
import IModel = Contents.IModel; 
import DangerousIcon from '@mui/icons-material/Dangerous';

interface IFileItemProps {
  file: { value: IModel; done: boolean };
  basePath: string;
  inContained: (file: string) => boolean;
  extraFileHelp: string;
  openFile: (path: string) => void;
  allowFiles?: boolean;
}



const FileItem = ({
  file,
  basePath,
  inContained,
  extraFileHelp,
  openFile,
  allowFiles
}: IFileItemProps) => {

  // TODO: this function is implemented twice -> in file list (to get missingFiles) and here to check inContained
  //  in my opinion this should only be declared once here to check both missing and contained status of the FileItem
  const getRelativePath = (file) => {
    // TODO: use basePath here to calculate relative path (basePath is props.path from file list) and see comment in file list for same function
    const regex = /assignments\/[^/]+\/(.+)/;
    const match = file.value.path.match(regex);
    return match ? match[1] : file.value.path;
  }

  return (
    <ListItem disablePadding>
      <ListItemButton onClick={() => openFile(file.value.path)} dense={true}>
        <ListItemIcon>
          <KeyboardArrowRightIcon sx={{visibility:'hidden'}}/>
          <InsertDriveFileRoundedIcon />
        </ListItemIcon>
        <ListItemText 
          primary={<Typography>{file.value.name}</Typography>}
          secondary={
            <Stack direction={'row'} spacing={2}>
              {!inContained(getRelativePath(file)) && !allowFiles && (
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