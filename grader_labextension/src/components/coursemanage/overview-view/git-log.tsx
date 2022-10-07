// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import { Lecture } from '../../../model/lecture';
import { Assignment } from '../../../model/assignment';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Divider,
  List,
  ListItem,
  ListItemText,
  Paper,
  Typography
} from '@mui/material';

import * as React from 'react';
import { getGitLog, IGitLogObject } from '../../../services/file.service';
import { utcToLocalFormat } from '../../../services/datetime.service';
import { RepoType } from '../../util/repo-type';

interface IGitLogProps {
  gitLogs: IGitLogObject[];
}

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

export const GitLog = (props: IGitLogProps) => {
  const [gitLogs, setGitLogs] = React.useState(props.gitLogs);
  React.useEffect(() => {
    setGitLogs(props.gitLogs);
  }, [props.gitLogs]);

  return (
    <Card elevation={3}>
      <CardHeader title="Git Log" />
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
  );
};
