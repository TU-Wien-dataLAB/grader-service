// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import * as React from 'react';
import {
  Box,
  Card,
  Button,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Paper,
  Typography,
  ListItemSecondaryAction
} from '@mui/material';
import { SxProps } from '@mui/system';
import { Theme } from '@mui/material/styles';
import { Submission } from '../../model/submission';
import ChatRoundedIcon from '@mui/icons-material/ChatRounded';
import {
  utcToLocalFormat,
  utcToTimestamp
} from '../../services/datetime.service';
import CloudDoneRoundedIcon from '@mui/icons-material/CloudDoneRounded';
import RestoreIcon from '@mui/icons-material/Restore';
import DeleteIcon from '@mui/icons-material/Delete';
import { grey } from '@mui/material/colors';
import { useNavigate } from 'react-router-dom';
import { showDialog } from '../util/dialog-provider';
import {
  deleteSubmission,
  restoreSubmission
} from '../../services/submissions.service';
import { Assignment } from '../../model/assignment';
import { Lecture } from '../../model/lecture';
import { enqueueSnackbar } from 'notistack';
import { queryClient } from '../../widgets/assignmentmanage';
import { FeedbackStatus } from '../../model/feedbackStatus';

/**
 * Props for SubmissionListComponent.
 */
interface ISubmissionListProps {
  lecture: Lecture;
  assignment: Assignment;
  submissions: Submission[];
  subLeft: number;
  sx?: SxProps<Theme>;
}

/**
 * Renders student submissions in a list
 * @param props Props of submission list component
 */
export const SubmissionList = (props: ISubmissionListProps) => {
  /**
   * Generates submission items which will be rendered in the list
   * and will be fed using the IIterator from the FilterFileBrowserModel
   * @param submissions student submissions
   *
   */

  const navigate = useNavigate();

  const generateItems = (submissions: Submission[]) => {
    return submissions
      .sort((a, b) =>
        utcToTimestamp(a.submitted_at) > utcToTimestamp(b.submitted_at) ? -1 : 1
      )
      .map(value => (
        <Box>
          <ListItem disablePadding>
            <ListItemIcon>
              <CloudDoneRoundedIcon sx={{ ml: 1 }} />
            </ListItemIcon>
            <ListItemText
              primary={utcToLocalFormat(value.submitted_at)}
              secondary={
                value.feedback_status === FeedbackStatus.Generated ||
                value.feedback_status === FeedbackStatus.FeedbackOutdated
                  ? `${value.score} Point` + (value.score === 1 ? '' : 's')
                  : null
              }
            />
            <ListItemSecondaryAction>
              {
                <Button
                  startIcon={<RestoreIcon />}
                  size="small"
                  onClick={() => {
                    showDialog(
                      'Restore Submission',
                      'Do you really want to revert the assignment state to this submission? This deletes all current changes you made!',
                      async () => {
                        try {
                          await restoreSubmission(
                            props.lecture.id,
                            props.assignment.id,
                            value.commit_hash
                          );
                          enqueueSnackbar('Successfully Restored Submission', {
                            variant: 'success'
                          });
                        } catch (e) {
                          if (e instanceof Error) {
                            enqueueSnackbar(
                              'Error Restore Submission: ' + e.message,
                              { variant: 'error' }
                            );
                          } else {
                            console.error(
                              'Error: cannot interpret type unknown as error',
                              e
                            );
                          }
                        }
                      }
                    );
                  }}
                >
                  Restore
                </Button>
              }
              {value.feedback_status === FeedbackStatus.NotGenerated && (
                <Button
                  sx={{ ml: 3 }}
                  startIcon={<DeleteIcon />}
                  size="small"
                  onClick={() => {
                    const warningMessage =
                      props.assignment.settings.max_submissions !== null &&
                      props.subLeft === 0 &&
                      props.submissions.length === 1
                        ? '<strong>This is your last submission that can be graded. If you delete it, you won’t be able to submit again, and you will receive 0 points.<strong></strong>'
                        : '';
                    showDialog(
                      'Delete Submission',
                      'Are you sure you want to delete this submission? Once deleted, you cannot undo this action. This will not affect the number of submissions you have remaining, if a maximum number of submissions is allowed.<br><br>' +
                        warningMessage,
                      async () => {
                        try {
                          await deleteSubmission(
                            props.lecture.id,
                            props.assignment.id,
                            value.id
                          );
                          await queryClient.invalidateQueries({
                            queryKey: ['submissions']
                          });
                          await queryClient.invalidateQueries({
                            queryKey: ['submissionsAssignmentStudent']
                          });
                          enqueueSnackbar('Successfully Deleted Submission', {
                            variant: 'success'
                          });
                        } catch (e) {
                          if (e instanceof Error) {
                            enqueueSnackbar(
                              'Error Delete Submission: ' + e.message,
                              { variant: 'error' }
                            );
                          } else {
                            console.error(
                              'Error: cannot interpret type unkown as error',
                              e
                            );
                          }
                        }
                      }
                    );
                  }}
                >
                  Delete Submission
                </Button>
              )}
              {value.feedback_status === FeedbackStatus.Generated ||
              value.feedback_status === FeedbackStatus.FeedbackOutdated ? (
                <Button
                  sx={{ ml: 3 }}
                  startIcon={<ChatRoundedIcon />}
                  size="small"
                  onClick={() => navigate(`feedback/${value.id}`)}
                >
                  Open feedback
                </Button>
              ) : null}
            </ListItemSecondaryAction>
          </ListItem>
        </Box>
      ));
  };

  return (
    <Paper elevation={0} sx={props.sx}>
      <Card sx={{ mt: 1 }} variant="outlined">
        {props.submissions.length === 0 ? (
          <Typography variant={'body1'} color={grey[500]} sx={{ ml: 1 }}>
            No Submissions Yet
          </Typography>
        ) : (
          <List dense={false}>{generateItems(props.submissions)}</List>
        )}
      </Card>
    </Paper>
  );
};
