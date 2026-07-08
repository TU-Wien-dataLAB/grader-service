import React from 'react';
import {
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Tooltip,
  Stack,
  Typography,
  Checkbox,
  Chip
} from '@mui/material';
import InsertDriveFileRoundedIcon from '@mui/icons-material/InsertDriveFileRounded';
import KeyboardArrowRightIcon from '@mui/icons-material/KeyboardArrowRight';
import DangerousIcon from '@mui/icons-material/Dangerous';
import {
  File,
  getRelativePath,
  getRemoteFileStatus
} from '../../services/file.service';
import { Lecture } from '../../model/lecture';
import { Assignment } from '../../model/assignment';
import { RepoType } from './repo-type';
import CompareArrowsIcon from '@mui/icons-material/CompareArrows';
import CheckIcon from '@mui/icons-material/Check';
import PublishRoundedIcon from '@mui/icons-material/PublishRounded';
import { UseQueryOptions, useQuery } from '@tanstack/react-query';
import { RemoteFileStatus } from '../../model/remoteFileStatus';
import WarningIcon from '@mui/icons-material/Warning';

interface IFileItemProps {
  file: File;
  lecture?: Lecture;
  assignment?: Assignment;
  inContained: (file: string) => boolean;
  missingFiles?: File[];
  extraFiles?: File[];
  openFile: (path: string) => void;
  checkboxes: boolean;
  onFileSelectChange?: (filePath: string, isSelected: boolean) => void;
  checkStatus?: boolean; // check if file is up to date with remote git repo
}

const FileItem = ({
  file,
  lecture,
  assignment,
  openFile,
  missingFiles,
  extraFiles,
  checkboxes,
  onFileSelectChange,
  checkStatus = false // Default is false if not provided
}: IFileItemProps) => {
  const inMissing = (filePath: string) => {
    return missingFiles?.some(missingFile => missingFile.path === filePath);
  };

  const inExtra = (filePath: string) => {
    return extraFiles?.some(extraFile => extraFile.path === filePath);
  };

  const [isSelected, setIsSelected] = React.useState(true);

  const fileStatusQueryOptions: UseQueryOptions<RemoteFileStatus, Error> = {
    queryKey: ['fileStatus', lecture?.id, assignment?.id, file.path],
    queryFn: () =>
      getRemoteFileStatus(
        lecture,
        assignment,
        RepoType.SOURCE,
        getRelativePath(file.path, 'source'),
        true
      ) as Promise<RemoteFileStatus>,
    enabled: checkStatus && !!lecture && !!assignment, // Enable only if checkStatus is true
    staleTime: 3000
  };

  const fileRemoteStatusResponse = useQuery(fileStatusQueryOptions);

  if (fileRemoteStatusResponse.isError) {
    console.error(
      'could not fetch remote status: ' + fileRemoteStatusResponse.error.message
    );
  }

  const fileRemoteStatus: RemoteFileStatus.StatusEnum | undefined =
    fileRemoteStatusResponse.data?.status;

  const getFileRemoteStatusText = (status: RemoteFileStatus.StatusEnum) => {
    if (status === RemoteFileStatus.StatusEnum.UpToDate) {
      return 'The local file is up to date with the file from remote repository.';
    } else if (status === RemoteFileStatus.StatusEnum.PushNeeded) {
      return 'You have made changes to this file locally, a push is needed.';
    } else if (status === RemoteFileStatus.StatusEnum.NoRemoteRepo) {
      return 'There is no remote repository yet. Push your assignment to create it.';
    } else {
      return 'The local and remote file are divergent.';
    }
  };

  const getStatusChip = (status: RemoteFileStatus.StatusEnum) => {
    if (status === RemoteFileStatus.StatusEnum.UpToDate) {
      return (
        <Chip
          sx={{ mb: 1.0 }}
          label={'Up To Date'}
          color="success"
          size="small"
          icon={<CheckIcon />}
        />
      );
    } else if (status === RemoteFileStatus.StatusEnum.PushNeeded) {
      return (
        <Chip
          sx={{ mb: 1.0 }}
          label={'Push Needed'}
          color="warning"
          size="small"
          icon={<PublishRoundedIcon />}
        />
      );
    } else if (status === RemoteFileStatus.StatusEnum.NoRemoteRepo) {
      return (
        <Chip
          sx={{ mb: 1.0 }}
          label={'No Remote Repository'}
          color="primary"
          size="small"
          icon={<CheckIcon />}
        />
      );
    } else {
      return (
        <Chip
          sx={{ mb: 1.0 }}
          label={'Divergent'}
          color="error"
          size="small"
          icon={<CompareArrowsIcon />}
        />
      );
    }
  };

  const toggleSelection = () => {
    setIsSelected(prevState => {
      const nextState = !prevState;
      // used only with checkboxes -> in source directory
      onFileSelectChange?.(getRelativePath(file.path, 'source'), nextState);
      return nextState;
    });
  };

  const missingFileHelp =
    'This file should be part of your assignment! Did you delete it?';

  const extraFileHelp =
    "This file is not part of your assignment and therefore won't be graded.";

  return (
    <ListItem disablePadding>
      {checkboxes && (
        <ListItemIcon>
          <Checkbox checked={isSelected} onChange={toggleSelection} />
        </ListItemIcon>
      )}
      <ListItemButton onClick={() => openFile(file.path)} dense={true}>
        <ListItemIcon>
          {!checkboxes && (
            <KeyboardArrowRightIcon sx={{ visibility: 'hidden' }} />
          )}
          <InsertDriveFileRoundedIcon />
        </ListItemIcon>
        <ListItemText
          primary={
            <Stack direction="row" spacing={1} alignItems="center">
              <Typography>{file.name}</Typography>
              {inExtra(file.path) && (
                <Tooltip title={extraFileHelp}>
                  <Chip
                    label={'Extra File'}
                    icon={<WarningIcon sx={{ color: 'yellow' }} />}
                  />
                </Tooltip>
              )}
            </Stack>
          }
          secondary={
            <Stack direction={'row'} spacing={2}>
              {checkboxes && checkStatus && fileRemoteStatus && (
                <Tooltip title={getFileRemoteStatusText(fileRemoteStatus)}>
                  {getStatusChip(fileRemoteStatus)}
                </Tooltip>
              )}
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
            </Stack>
          }
        />
      </ListItemButton>
    </ListItem>
  );
};

export default FileItem;
