// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import {
  Box,
  Button,
  Card,
  CardContent,
  CardHeader,
  Divider,
  List,
  ListItem,
  ListItemText,
  Modal,
  Paper,
  Tooltip,
  Typography
} from '@mui/material';

import * as React from 'react';
import { IGitLogObject, getGitLog } from '../../../services/file.service';
import { utcToLocalFormat } from '../../../services/datetime.service';
import GitHubIcon from '@mui/icons-material/GitHub';
import { RepoType } from '../../util/repo-type';
import { useQuery } from '@tanstack/react-query';
import { Lecture } from '../../../model/lecture';
import { Assignment } from '../../../model/assignment';

interface IGitLogProps {
  lecture: Lecture;
  assignment: Assignment;
}

const style = {
  position: 'absolute' as const,
  top: '50%',
  left: '50%',
  transform: 'translate(-50%, -50%)',
  width: 400,
  boxShadow: 3,
  pt: 2,
  px: 4,
  pb: 3
};

const getTimelineItem = (logItem: IGitLogObject) => {
  const date = utcToLocalFormat(logItem.date);
  return (
    <Box>
      <ListItem>
        <ListItemText
          primary={logItem.commit_msg}
          secondary={'Author: ' + logItem.author + ', Date: ' + date}
        />
      </ListItem>
      <Divider />
    </Box>
  );
};

export const GitLogModal = (props: IGitLogProps) => {
  const { data: gitLogs = [] as IGitLogObject[], refetch: refetchGitLogs } =
    useQuery({
      queryKey: ['gitLogs', props.lecture, props.assignment],
      queryFn: () =>
        getGitLog(props.lecture, props.assignment, RepoType.SOURCE, 10)
    });

  const [open, setOpen] = React.useState(false);

  const handleOpen = async () => {
    setOpen(true);
    await refetchGitLogs();
  };

  const handleClose = () => {
    setOpen(false);
  };

  return (
    <React.Fragment>
      <Tooltip title={'Show Git Log'}>
        <Button
          onClick={handleOpen}
          variant="outlined"
          size="small"
          sx={{ ml: 1 }}
        >
          <GitHubIcon fontSize="small" sx={{ mr: 1 }} />
          Git Log
        </Button>
      </Tooltip>

      <Modal open={open} onClose={handleClose}>
        <Box sx={{ ...style }}>
          <CardHeader title="Git Log" />
          <Card elevation={0}>
            <CardContent sx={{ height: '300px', overflowY: 'auto' }}>
              <List sx={{ ml: 1, mr: 1 }}>
                {gitLogs.length > 0 ? (
                  gitLogs.map(log => getTimelineItem(log))
                ) : (
                  <Paper variant={'outlined'}>
                    <Typography>No commits yet!</Typography>
                  </Paper>
                )}
              </List>
            </CardContent>
          </Card>
          <Button sx={{}} onClick={handleClose}>
            Close
          </Button>
        </Box>
      </Modal>
    </React.Fragment>
  );
};
