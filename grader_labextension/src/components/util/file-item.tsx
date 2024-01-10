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
import DangerousIcon from '@mui/icons-material/Dangerous';
import {File, getRelativePathAssignment} from '../../services/file.service';

interface IFileItemProps {
  file: File;
  inContained: (file: string) => boolean;
  missingFiles?: File[],
  extraFileHelp: string;
  missingFileHelp: string;
  openFile: (path: string) => void;
  allowFiles?: boolean;
}

const FileItem = ({
  file,
  inContained,
  extraFileHelp,
  missingFileHelp,
  openFile,
  allowFiles,
  missingFiles,
}: IFileItemProps) => {

  const inMissing = (filePath: string) => {
    return missingFiles.some((missingFile) => missingFile.path === filePath);
  };

  //console.log("Missing files (file-item): " + missingFiles.map(f => f.path));
  return (
    <ListItem disablePadding>
      <ListItemButton onClick={() => openFile(file.path)} dense={true}>
        <ListItemIcon>
          <KeyboardArrowRightIcon sx={{visibility:'hidden'}}/>
          <InsertDriveFileRoundedIcon />
        </ListItemIcon>
        <ListItemText 
          primary={<Typography>{file.name}</Typography>}
          secondary=
          {
            <Stack direction={'row'} spacing={2}>
              {inMissing(file.path) && (
                <Tooltip title={missingFileHelp}>
                  <Stack direction={'row'} spacing={2} flex={0}>
                    <DangerousIcon color={'error'} fontSize={'small'} />
                    <Typography sx={{ whiteSpace: 'nowrap', minWidth: 'auto' }}>
                      Missing File
                    </Typography>
                  </Stack>
                </Tooltip>
              )}
              {
            <Stack direction={'row'} spacing={2}>
              {!inContained(getRelativePathAssignment(file.path)) && !allowFiles && (
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
            </Stack>
          }
        />
      </ListItemButton>
    </ListItem>
  );
};

export default FileItem;