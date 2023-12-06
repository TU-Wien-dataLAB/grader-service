import React, { useState } from 'react';
import {
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Collapse,
  Stack,
  Tooltip,
  Typography,
  List,
} from '@mui/material';
import { Contents } from '@jupyterlab/services';
import IModel = Contents.IModel; 
import FolderIcon from '@mui/icons-material/Folder';
import FileItem from './file-item';
import KeyboardArrowRightIcon from '@mui/icons-material/KeyboardArrowRight';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import { getFiles } from '../../services/file.service';

interface IFolderItemProps {
  folder: { value: IModel; done: boolean };
  inContained: (file: string) => boolean;
  extraFileHelp: string;
  missingFileHelp: string;
  openFile: (path: string) => void;
  allowFiles?: boolean;
}


const FolderItem = ({
  folder,
  inContained,
  extraFileHelp,
  missingFileHelp,
  openFile,
  allowFiles,
}) => {
  const [open, setOpen] = useState(false);

  const [nestedFiles, setNestedFiles] = useState([]);

  const handleToggle = async () => {
    if (!open) {
      try {
        const nestedFiles = await getFiles(folder.value.path);
        setNestedFiles(nestedFiles);
      } catch (error) {
        console.error('Error fetching nested files:', error);
      }
    }
    setOpen(!open);
  };

  return (
    <>
      <ListItem disablePadding>
        <ListItemButton onClick={handleToggle} dense={true}>
          <ListItemIcon>
          {open ? (
              <KeyboardArrowUpIcon />
            ) : (
              <KeyboardArrowRightIcon />
            )}
            <FolderIcon />
          </ListItemIcon>
          <ListItemText
            primary={<Typography>{folder.value.name}</Typography>}
          />
        </ListItemButton>
      </ListItem>
      <Collapse in={open} timeout="auto" unmountOnExit>
        <List sx={{ml: 3}}>
        {nestedFiles.length > 0 &&
          nestedFiles.map((file) =>
            file.value.type === 'directory' ? (
              <FolderItem
                key={file.value.path}
                folder={file}
                inContained={inContained}
                extraFileHelp={extraFileHelp}
                missingFileHelp={missingFileHelp}
                openFile={openFile}
                allowFiles={allowFiles}
              />
            ) : (
              <FileItem
                key={file.value.path}
                file={file}
                inContained={inContained}
                extraFileHelp={extraFileHelp}
                openFile={openFile}
                allowFiles={allowFiles}
               
              />
            )
          )}
        </List>
     
      </Collapse>
    </>
  );
};

export default FolderItem;
