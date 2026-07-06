import React, { useState } from 'react';
import {
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Collapse,
  Typography,
  List
} from '@mui/material';
import FolderIcon from '@mui/icons-material/Folder';
import FileItem from './file-item';
import KeyboardArrowRightIcon from '@mui/icons-material/KeyboardArrowRight';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import { getFiles } from '../../services/file.service';

const FolderItem = ({
  folder,
  lecture,
  assigment,
  missingFiles,
  extraFiles,
  inContained,
  openFile,
  checkboxes,
  onFileSelectChange,
  checkStatus
}) => {
  const [open, setOpen] = useState(false);

  const [nestedFiles, setNestedFiles] = useState([]);

  const missingFilesByDirectory = missingFiles.reduce((acc, missingFile) => {
    const directoryPath = missingFile.path.substring(
      0,
      missingFile.path.lastIndexOf('/')
    );
    if (!acc[directoryPath]) {
      acc[directoryPath] = [];
    }
    acc[directoryPath].push(missingFile);
    return acc;
  }, {});

  const handleToggle = async () => {
    if (!open) {
      try {
        const nestedFiles = await getFiles(folder.path);
        const missingFilesForDirectory =
          missingFilesByDirectory[folder.path] || [];
        // Update nested files with missing files if there are any that should be in this folder
        const folderContents = nestedFiles.concat(missingFilesForDirectory);
        setNestedFiles(folderContents);
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
            {open ? <KeyboardArrowUpIcon /> : <KeyboardArrowRightIcon />}
            <FolderIcon />
          </ListItemIcon>
          <ListItemText primary={<Typography>{folder.name}</Typography>} />
        </ListItemButton>
      </ListItem>
      <Collapse in={open} timeout="auto" unmountOnExit>
        <List sx={{ ml: 3 }}>
          {nestedFiles.length > 0 &&
            nestedFiles.map(file =>
              file.type === 'directory' ? (
                <FolderItem
                  key={file.path}
                  folder={file}
                  lecture={lecture}
                  assigment={assigment}
                  missingFiles={missingFiles || []}
                  extraFiles={extraFiles || []}
                  inContained={inContained}
                  openFile={openFile}
                  checkboxes={checkboxes}
                  onFileSelectChange={onFileSelectChange}
                  checkStatus={checkStatus}
                />
              ) : (
                <FileItem
                  key={file.path}
                  file={file}
                  lecture={lecture}
                  assignment={assigment}
                  missingFiles={missingFiles || []}
                  inContained={inContained}
                  openFile={openFile}
                  checkboxes={checkboxes}
                  onFileSelectChange={onFileSelectChange}
                  checkStatus={checkStatus}
                />
              )
            )}
        </List>
      </Collapse>
    </>
  );
};

export default FolderItem;
