// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.
import * as React from 'react';
import { Assignment } from '../../../model/assignment';
import { Lecture } from '../../../model/lecture';
import {
  generateAssignment,
  pullAssignment,
  pushAssignment
} from '../../../services/assignments.service';
import GetAppRoundedIcon from '@mui/icons-material/GetAppRounded';
import OpenInBrowserIcon from '@mui/icons-material/OpenInBrowser';
import { CommitDialog } from '../../util/dialog';
import {
  Box,
  Button,
  Card,
  CardActions,
  CardContent,
  CardHeader,
  Chip,
  Divider,
  IconButton,
  ToggleButton,
  ToggleButtonGroup,
  Tooltip
} from '@mui/material';
import ReplayIcon from '@mui/icons-material/Replay';
import TerminalIcon from '@mui/icons-material/Terminal';
import AddIcon from '@mui/icons-material/Add';
import CheckIcon from '@mui/icons-material/Check';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import { FilesList } from '../../util/file-list';
import { GlobalObjects } from '../../../index';
import { Contents } from '@jupyterlab/services';
import { openBrowser, openTerminal } from '../overview/util';
import { PageConfig } from '@jupyterlab/coreutils';
import PublishRoundedIcon from '@mui/icons-material/PublishRounded';
import {
  getFiles,
  getRemoteStatus,
  lectureBasePath
} from '../../../services/file.service';
import { RepoType } from '../../util/repo-type';
import { enqueueSnackbar } from 'notistack';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { loadString, storeString } from '../../../services/storage.service';
import { queryClient } from '../../../widgets/assignmentmanage';
import { RemoteFileStatus } from '../../../model/remoteFileStatus';
import { GitLogModal } from './git-log';

export interface IFilesProps {
  lecture: Lecture;
  assignment: Assignment;
  onAssignmentChange: (assignment: Assignment) => void;
}

export const Files = ({
  lecture,
  assignment,
  onAssignmentChange
}: IFilesProps) => {
  const navigate = useNavigate();
  const reloadPage = () => navigate(0);
  const serverRoot = PageConfig.getOption('serverRoot');

  const { data: selectedDir = 'source', refetch: refetchSelectedDir } =
    useQuery({
      queryKey: ['selectedDir'],
      queryFn: async () => {
        const data = loadString('files-selected-dir');
        // default to 'source' if no value is stored
        return data || 'source';
      }
    });

  const { data: repoStatus, refetch: refetchRepoStatus } = useQuery({
    queryKey: ['repoStatus', lecture.id, assignment.id],
    queryFn: async () => {
      const response = await getRemoteStatus(
        lecture,
        assignment,
        RepoType.SOURCE,
        true
      );
      return response.status;
    }
  });

  const { data: files = [], refetch: refetchFiles } = useQuery({
    queryKey: ['files', lecture.id, assignment.id, selectedDir],
    queryFn: async () => {
      const path = `${lectureBasePath}${lecture.code}/${selectedDir}/${assignment.id}`;
      return await getFiles(path);
    }
  });

  // open the selected directory on load
  openBrowser(
    `${lectureBasePath}${lecture.code}/${selectedDir}/${assignment.id}`
  );

  React.useEffect(() => {
    const srcPath = `${lectureBasePath}${lecture.code}/source/${assignment.id}`;
    GlobalObjects.docManager.services.contents.fileChanged.connect(
      (sender: Contents.IManager, change: Contents.IChangedArgs) => {
        const { oldValue, newValue } = change;
        if (
          (newValue && !newValue.path.includes(srcPath)) ||
          (oldValue && !oldValue.path.includes(srcPath))
        ) {
          return;
        }
        reloadPage();
        refetchRepoStatus();
        refetchFiles();
      }
    );
  }, [assignment, lecture]);

  const handleSwitchDir = async (dir: 'source' | 'release') => {
    if (dir === selectedDir) return;
    if (dir === 'release') {
      try {
        await generateAssignment(lecture.id, assignment);
        enqueueSnackbar('Generated Student Version Notebooks', {
          variant: 'success'
        });
        await setSelectedDir(dir);
      } catch (error: any) {
        enqueueSnackbar(`Error Generating Notebooks: ${error.message}`, {
          variant: 'error'
        });
      }
    } else {
      await setSelectedDir(dir);
    }
  };

  const setSelectedDir = async (dir: 'source' | 'release') => {
    storeString('files-selected-dir', dir);
    refetchSelectedDir().then(() => {
      openBrowser(
        `${lectureBasePath}${lecture.code}/${selectedDir}/${assignment.id}`
      );
    });
  };

  const handlePushAssignment = async (
    commitMessage: string,
    selectedFiles: string[]
  ) => {
    try {
      await pushAssignment(
        lecture.id,
        assignment.id,
        RepoType.RELEASE,
        commitMessage,
        selectedFiles
      );
      await pushAssignment(
        lecture.id,
        assignment.id,
        RepoType.SOURCE,
        commitMessage,
        selectedFiles
      );
      await queryClient.invalidateQueries({ queryKey: ['assignments'] });
      enqueueSnackbar('Successfully Pushed Assignment', { variant: 'success' });
      refetchRepoStatus();
      refetchFiles();
    } catch (err) {
      enqueueSnackbar(`Error Pushing Assignment: ${err}`, { variant: 'error' });
    }
  };

  const handlePullAssignment = async () => {
    try {
      await pullAssignment(lecture.id, assignment.id, RepoType.SOURCE);
      enqueueSnackbar('Successfully Pulled Assignment', { variant: 'success' });
      refetchRepoStatus();
      refetchFiles();
    } catch (err) {
      enqueueSnackbar(`Error Pulling Assignment: ${err}`, { variant: 'error' });
    }
  };

  const newUntitled = async () => {
    const res = await GlobalObjects.docManager.newUntitled({
      type: 'notebook',
      path: `${lectureBasePath}${lecture.code}/source/${assignment.id}`
    });
    GlobalObjects.docManager.openOrReveal(res.path);
  };

  const getStatusChip = (status: RemoteFileStatus.StatusEnum) => {
    const statusMap: Record<
      RemoteFileStatus.StatusEnum,
      {
        label: string;
        color:
          | 'default'
          | 'primary'
          | 'secondary'
          | 'error'
          | 'warning'
          | 'info'
          | 'success';
        icon: JSX.Element;
      }
    > = {
      UP_TO_DATE: {
        label: 'Up To Date',
        color: 'success',
        icon: <CheckIcon />
      },
      PULL_NEEDED: {
        label: 'Pull Needed',
        color: 'warning',
        icon: <GetAppRoundedIcon />
      },
      PUSH_NEEDED: {
        label: 'Push Needed',
        color: 'warning',
        icon: <PublishRoundedIcon />
      },
      DIVERGENT: {
        label: 'Divergent',
        color: 'error',
        icon: <ErrorOutlineIcon />
      },
      NO_REMOTE_REPO: {
        label: 'No Remote Repository',
        color: 'primary',
        icon: <CheckIcon />
      }
    };

    // Fallback if the status is not in the statusMap (it should be)
    const { label, color, icon } = statusMap[status] || {};

    // Return the Chip component with appropriate props or null if status is invalid
    return label ? (
      <Chip
        sx={{ mb: 1 }}
        label={label}
        color={color}
        size="small"
        icon={icon}
      />
    ) : null;
  };

  const getRemoteStatusText = (status: RemoteFileStatus.StatusEnum) => {
    switch (status) {
      case RemoteFileStatus.StatusEnum.UpToDate:
        return 'The local files are up to date with the remote repository.';
      case RemoteFileStatus.StatusEnum.PullNeeded:
        return 'The remote repository has new changes. Pull now to update your local files.';
      case RemoteFileStatus.StatusEnum.PushNeeded:
        return 'You have made changes to your local repository which you can push.';
      case RemoteFileStatus.StatusEnum.Divergent:
        return 'The local and remote files are divergent.';
      case RemoteFileStatus.StatusEnum.NoRemoteRepo:
        return 'There is no remote repository yet. Push your assignment to create it.';
      default:
        return '';
    }
  };

  return (
    <Card
      sx={{
        overflow: 'hidden',
        m: 3,
        flex: 1,
        borderRadius: 2,
        boxShadow: 3,
        display: 'flex',
        flexDirection: 'column'
      }}
    >
      <CardHeader
        title="Manage Assignment Files"
        action={
          <Tooltip title="Reload">
            <IconButton onClick={reloadPage}>
              <ReplayIcon />
            </IconButton>
          </Tooltip>
        }
        subheader={
          repoStatus && (
            <Tooltip title={getRemoteStatusText(repoStatus)}>
              {getStatusChip(repoStatus)}
            </Tooltip>
          )
        }
        slotProps={{
          title: { display: 'inline' },
          subheader: { display: 'inline', ml: 2 }
        }}
      />
      <Divider />
      <Box sx={{ display: 'flex', width: '100%', alignItems: 'center', p: 2 }}>
        <ToggleButtonGroup
          value={selectedDir}
          exclusive
          onChange={(e, dir) => handleSwitchDir(dir)}
          sx={{ flex: 1 }}
        >
          <Tooltip
            title={
              'Source code version of notebooks with grading cells. Add notebooks or files to the file browser, and they will appear in the file list below. You can edit your notebooks, add grading cells, assign points, and create tests for your students.'
            }
          >
            <ToggleButton
              value="source"
              aria-label="Source code view"
              disabled={selectedDir === 'source'}
              sx={{
                flex: 1,
                '&.Mui-selected': {
                  color: 'primary.main',
                  fontWeight: 'bold'
                }
              }}
            >
              Source Code
            </ToggleButton>
          </Tooltip>
          <Tooltip
            title={
              'Clicking this button displays a preview of the student version of the source notebooks. The notebooks will be shown in the file list below the way students will see them.'
            }
          >
            <ToggleButton
              value="release"
              aria-label="Student version view"
              disabled={selectedDir === 'release'}
              sx={{
                flex: 1,
                '&.Mui-selected': {
                  color: 'primary.main',
                  fontWeight: 'bold'
                }
              }}
            >
              Student Version
            </ToggleButton>
          </Tooltip>
        </ToggleButtonGroup>
      </Box>
      <Divider />
      <CardContent sx={{ flex: 1, overflowY: 'auto', p: 2 }}>
        <FilesList
          files={files}
          lecture={lecture}
          assignment={assignment}
          checkboxes={false}
        />
      </CardContent>
      <Divider />
      <CardActions
        sx={{ justifyContent: 'space-between', flexWrap: 'wrap', p: 2 }}
      >
        <Box sx={{ display: 'flex', gap: 1 }}>
          <CommitDialog
            handleCommit={handlePushAssignment}
            lecture={lecture}
            assignment={assignment}
          >
            <Button
              variant={repoStatus === 'PUSH_NEEDED' ? 'contained' : 'outlined'}
              color={repoStatus === 'PUSH_NEEDED' ? 'warning' : 'primary'}
            >
              <PublishRoundedIcon sx={{ mr: 1 }} /> Push Changes
            </Button>
          </CommitDialog>
          <Button
            variant={repoStatus === 'PULL_NEEDED' ? 'contained' : 'outlined'}
            color={repoStatus === 'PULL_NEEDED' ? 'warning' : 'primary'}
            onClick={handlePullAssignment}
          >
            <GetAppRoundedIcon sx={{ mr: 1 }} /> Pull Changes
          </Button>
        </Box>
        <Box>
          <Button variant="outlined" onClick={newUntitled}>
            <AddIcon sx={{ mr: 1 }} /> New Notebook
          </Button>
          <GitLogModal lecture={lecture} assignment={assignment} />
          <IconButton
            onClick={() =>
              openBrowser(
                `${lectureBasePath}${lecture.code}/${selectedDir}/${assignment.id}`
              )
            }
          >
            <OpenInBrowserIcon />
          </IconButton>
          <IconButton
            onClick={() =>
              openTerminal(
                `${serverRoot}/${lectureBasePath}${lecture.code}/${selectedDir}/${assignment.id}`
              )
            }
          >
            <TerminalIcon />
          </IconButton>
        </Box>
      </CardActions>
    </Card>
  );
};
