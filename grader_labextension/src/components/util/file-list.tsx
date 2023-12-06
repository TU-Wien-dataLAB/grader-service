import React from 'react';
import {
  Box,
  Card,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Paper,
  Tooltip,
  Typography,
} from '@mui/material';
import { Contents } from '@jupyterlab/services';
import IModel = Contents.IModel;
import { Stack, SxProps } from '@mui/system';
import { Theme } from '@mui/material/styles';
import { getFiles, openFile } from '../../services/file.service';
import { grey } from '@mui/material/colors';
import FileItem from './file-item';
import FolderItem from './folder-item';
import { Assignment } from '../../model/assignment';
import InsertDriveFileRoundedIcon from '@mui/icons-material/InsertDriveFileRounded';
import DangerousIcon from '@mui/icons-material/Dangerous';

interface IFileListProps {
  path: string;
  sx?: SxProps<Theme>;
  shouldContain?: string[];
  assignment?: Assignment;
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

  const generateItems = (files) => {
    const fileNames = files.map((file) => file.value.name);
    const missingFiles =
      props.shouldContain &&
      props.shouldContain.filter((f) => !fileNames.includes(f));
  
    const items = files.map((file) =>
      file.value.type === 'directory' ? (
        <FolderItem
          key={file.value.path}
          folder={file}
          inContained={inContained}
          extraFileHelp={extraFileHelp}
          missingFileHelp={missingFileHelp}
          openFile={openFile}
          allowFiles={props.assignment?.allow_files}
        />
      ) : (
        <FileItem
          key={file.value.path}
          file={file}
          inContained={inContained}
          extraFileHelp={extraFileHelp}
          openFile={openFile}
          allowFiles={props.assignment?.allow_files}
        />
      )
    );
  
    if (missingFiles && missingFiles.length > 0) {
      const missingFileItems = missingFiles.map((file) => (
        <ListItem disablePadding key={file}>
          <ListItem>
            <ListItemIcon>
              <InsertDriveFileRoundedIcon color={'disabled'} />
            </ListItemIcon>
            <ListItemText
              primary={<Typography color={'text.secondary'}>{file}</Typography>}
              secondary={
                <Stack direction={'row'} spacing={2}>
                  <Tooltip title={missingFileHelp}>
                    <Stack direction={'row'} spacing={2} flex={0}>
                      <DangerousIcon color={'error'} fontSize={'small'} />
                      <Typography sx={{ whiteSpace: 'nowrap', minWidth: 'auto' }}>
                        File Missing
                      </Typography>
                    </Stack>
                  </Tooltip>
                </Stack>
              }
            />
          </ListItem>
        </ListItem>
      ));
  
      return [...items, ...missingFileItems];
    }
  
    return items;
  };
  
  return (
    <Paper elevation={0} sx={props.sx}>
      <Card sx={{ mt: 1, mb: 1, overflow: 'auto' }} variant="outlined">
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
