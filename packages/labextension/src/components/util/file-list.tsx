import React from 'react';
import { Card, List, Paper, Typography } from '@mui/material';
import { SxProps } from '@mui/system';
import { Theme } from '@mui/material/styles';
import {
  openFile,
  File,
  extractRelativePaths,
  getRelativePath,
  lectureBasePath
} from '../../services/file.service';
import { grey } from '@mui/material/colors';
import FileItem from './file-item';
import FolderItem from './folder-item';
import { Assignment } from '../../model/assignment';
import { Lecture } from '../../model/lecture';
import picomatch from 'picomatch';

interface IFileListProps {
  files: File[];
  sx?: SxProps<Theme>;
  shouldContain?: string[];
  assignment?: Assignment;
  lecture?: Lecture;
  missingFiles?: File[];
  checkboxes: boolean;
  onFileSelectChange?: (filePath: string, isSelected: boolean) => void;
  checkStatus?: boolean;
}

export const FilesList = (props: IFileListProps) => {
  const inContained = (file: string) => {
    if (props.shouldContain) {
      return props.shouldContain.includes(file);
    }
    return true;
  };

  const generateItems = (files: File[], handleFileSelectChange) => {
    const filePaths: string[] = files.flatMap(file =>
      extractRelativePaths(file, 'assignments')
    );

    const missingFiles =
      props.shouldContain
        ?.filter(f => !filePaths.includes(f))
        .map(missingFile => ({
          name:
            missingFile.substring(missingFile.lastIndexOf('/') + 1) ||
            missingFile,
          path:
            `${lectureBasePath}${props.lecture.code}/assignments/${props.assignment.id}/` +
            missingFile,
          type: 'file',
          content: []
        })) || [];
    const extraFiles = filePaths
      .filter(
        f =>
          !props.shouldContain?.includes(f) &&
          !picomatch.isMatch(f, props.assignment?.settings?.allowed_files)
      )
      .map(extraFile => ({
        name: extraFile.substring(extraFile.lastIndexOf('/') + 1) || extraFile,
        path:
          `${lectureBasePath}${props.lecture.code}/assignments/${props.assignment.id}/` +
          extraFile,
        type: 'file',
        content: []
      }));
    const topLevelMissing = missingFiles.filter(missingFile => {
      const relativePath = getRelativePath(missingFile.path, 'assignments');
      return !relativePath.includes('/');
    });

    const allFiles = files.concat(topLevelMissing);

    return allFiles.map((file: File) =>
      file.type === 'directory' ? (
        <FolderItem
          key={file.path}
          folder={file}
          lecture={props.lecture}
          assigment={props.assignment}
          missingFiles={missingFiles}
          extraFiles={extraFiles}
          inContained={inContained}
          openFile={openFile}
          checkboxes={props.checkboxes}
          onFileSelectChange={handleFileSelectChange}
          checkStatus={props.checkStatus}
        />
      ) : (
        <FileItem
          key={file.path}
          file={file}
          lecture={props.lecture}
          assignment={props.assignment}
          missingFiles={missingFiles}
          extraFiles={extraFiles}
          inContained={inContained}
          openFile={openFile}
          checkboxes={props.checkboxes}
          onFileSelectChange={handleFileSelectChange}
          checkStatus={props.checkStatus}
        />
      )
    );
  };

  return (
    <Paper elevation={0} sx={props.sx}>
      <Card sx={{ mt: 1, mb: 1, overflow: 'auto' }} variant="outlined">
        {props.files.length === 0 ? (
          <Typography variant="body1" color={grey[500]} sx={{ ml: 1 }}>
            No Files Found
          </Typography>
        ) : (
          <List dense={false}>
            {generateItems(props.files, props.onFileSelectChange)}
          </List>
        )}
      </Card>
    </Paper>
  );
};
