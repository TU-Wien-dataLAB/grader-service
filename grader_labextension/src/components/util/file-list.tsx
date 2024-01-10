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
import { getFiles, openFile, File, extractRelativePathsAssignment, getRelativePathAssignment, lectureBasePath} from '../../services/file.service';
import { grey } from '@mui/material/colors';
import FileItem from './file-item';
import FolderItem from './folder-item';
import { Assignment } from '../../model/assignment';
import { Lecture } from '../../model/lecture';


interface IFileListProps {
  path: string;
  sx?: SxProps<Theme>;
  shouldContain?: string[];
  assignment?: Assignment;
  lecture?: Lecture;
  missingFiles?: File[];
}



export const FilesList = (props: IFileListProps) => {
  const [files, setFiles] = React.useState([]);


  React.useEffect(() => {
    getFiles(props.path).then((files) => setFiles(files));
  }, [props]);


  const inContained = (file: string) => {
    if (props.shouldContain) {
      return props.shouldContain.filter(f => file === f).length > 0;
    }
    return true;
  };

  
  const extraFileHelp = `This file is not part of the assignment and will be removed when grading! Did you rename a notebook file or add it manually?`;
  const missingFileHelp = `This file should be part of your assignment! Did you delete it?`;

  const generateItems = (files: File[]) => {
   
    const filePaths = files.flatMap((file) => extractRelativePathsAssignment(file));
    const missingFiles : File[] =
    (props.shouldContain &&
    props.shouldContain
      .filter((f) => !filePaths.includes(f))
      .map((missingFile) => ({
        name: missingFile.substring(missingFile.lastIndexOf("/") + 1) || missingFile, 
        path: `${lectureBasePath}${props.lecture.code}/assignments/${props.assignment.id}/` + missingFile, 
        type: 'file', 
        content: [], 
      }))) || [];

      const missingFilesTopOrder = missingFiles.filter((missingFile) => {
        const relativePath = getRelativePathAssignment(missingFile.path);
        return !relativePath.includes('/');
      });

    
    const items = files.concat(missingFilesTopOrder).map((file: File) => {
      if (file.type === 'directory') {
        
        return (
          <FolderItem
            key={file.path}
            folder={file}
            missingFiles={missingFiles || []}
            missingFileHelp={missingFileHelp}
            inContained={inContained}
            extraFileHelp={extraFileHelp}
            openFile={openFile}
            allowFiles={props.assignment?.allow_files}
          />
        );
      } else {
        return (
          <FileItem
            key={file.path}
            file={file}
            missingFiles={missingFiles || []}
            missingFileHelp={missingFileHelp}
            inContained={inContained}
            extraFileHelp={extraFileHelp}
            openFile={openFile}
            allowFiles={props.assignment?.allow_files}
          />
        );
      }
    });
  
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


