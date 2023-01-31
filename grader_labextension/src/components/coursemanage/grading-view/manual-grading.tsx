// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import { ModalTitle } from '../../util/modal-title';
import {
  Box,
  Button,
  IconButton,
  Stack,
  Tooltip,
  Typography
} from '@mui/material';
import * as React from 'react';
import { Lecture } from '../../../model/lecture';
import { Assignment } from '../../../model/assignment';
import { Submission } from '../../../model/submission';
import {
  getProperties,
  updateSubmission
} from '../../../services/submissions.service';
import { GradeBook } from '../../../services/gradebook';
import { createManualFeedback } from '../../../services/grading.service';
import { FilesList } from '../../util/file-list';
import { AgreeDialog } from '../../util/dialog';
import ReplayIcon from '@mui/icons-material/Replay';
import { enqueueSnackbar } from 'notistack';

export interface IManualGradingProps {
  lecture: Lecture;
  assignment: Assignment;
  submission: Submission;
  username: string;
  onClose: () => void;
}

export const ManualGrading = (props: IManualGradingProps) => {
  const [gradeBook, setGradeBook] = React.useState(null);
  const [path, setPath] = React.useState(null);
  const [showDialog, setShowDialog] = React.useState(false);
  const [dialogContent, setDialogContent] = React.useState({
    title: '',
    message: '',
    handleAgree: null,
    handleDisagree: null
  });
  React.useEffect(() => {
    reloadProperties();
    createManualFeedback(
      props.lecture.id,
      props.assignment.id,
      props.submission.id
    ).then(() => {
      const manualPath = `manualgrade/${props.lecture.code}/${props.assignment.id}/${props.submission.id}`;
      setPath(manualPath);
    });
  }, [props.lecture, props.assignment, props.submission]);

  const openFinishDialog = () => {
    setDialogContent({
      title: 'Confirm Grading',
      message: 'Do you want to save the assignment grading?',
      handleAgree: finishGrading,
      handleDisagree: () => {
        setShowDialog(false);
      }
    });
    setShowDialog(true);
  };

  const finishGrading = () => {
    props.submission.manual_status = 'manually_graded';
    updateSubmission(
      props.lecture.id,
      props.assignment.id,
      props.submission.id,
      props.submission
    ).then(
      response => {
        props.onClose();
      },
      err => {
        enqueueSnackbar(err.message, {
          variant: 'error'
        });
      }
    );
  };

  const reloadProperties = () => {
    getProperties(
      props.lecture.id,
      props.assignment.id,
      props.submission.id
    ).then(properties => {
      const gradeBook = new GradeBook(properties);
      setGradeBook(gradeBook);
    });
  };

  return (
    <Box>
      <ModalTitle title={'Manual Grading ' + props.assignment.id} />
      <Box sx={{ m: 2, mt: 12 }}>
        <Stack direction="row" spacing={2} sx={{ ml: 2 }}>
          <Stack sx={{ mt: 0.5 }}>
            <Typography
              textAlign="right"
              color="text.secondary"
              sx={{ fontSize: 12, height: 35 }}
            >
              Username
            </Typography>
            <Typography
              textAlign="right"
              color="text.secondary"
              sx={{ fontSize: 12, height: 35 }}
            >
              Lecture
            </Typography>
            <Typography
              textAlign="right"
              color="text.secondary"
              sx={{ fontSize: 12, height: 35 }}
            >
              Assignment
            </Typography>
            <Typography
              textAlign="right"
              color="text.secondary"
              sx={{ fontSize: 12, height: 35 }}
            >
              Points
            </Typography>
            <Typography
              textAlign="right"
              color="text.secondary"
              sx={{ fontSize: 12, height: 35 }}
            >
              Extra Credit
            </Typography>
          </Stack>
          <Stack>
            <Typography
              color="text.primary"
              sx={{ display: 'inline-block', fontSize: 16, height: 35 }}
            >
              {props.username}
            </Typography>
            <Typography
              color="text.primary"
              sx={{ display: 'inline-block', fontSize: 16, height: 35 }}
            >
              {props.lecture.name}
            </Typography>
            <Typography
              color="text.primary"
              sx={{ display: 'inline-block', fontSize: 16, height: 35 }}
            >
              {props.assignment.name}
              <Typography
                color="text.secondary"
                sx={{
                  display: 'inline-block',
                  fontSize: 14,
                  ml: 2,
                  height: 35
                }}
              >
                {props.assignment.type}
              </Typography>
            </Typography>
            <Typography
              color="text.primary"
              sx={{ display: 'inline-block', fontSize: 16, height: 35 }}
            >
              {gradeBook?.getPoints()}
              <Typography
                color="text.secondary"
                sx={{ display: 'inline-block', fontSize: 14, ml: 0.25 }}
              >
                /{gradeBook?.getMaxPoints()}
              </Typography>
            </Typography>
            <Typography
              color="text.primary"
              sx={{ display: 'inline-block', fontSize: 16, height: 35 }}
            >
              {gradeBook?.getExtraCredits()}
            </Typography>
          </Stack>
        </Stack>
      </Box>
      <Typography sx={{ m: 2, mb: 0 }}>Submission Files</Typography>
      <Box maxHeight={200} sx={{ overflowY: 'auto' }}>
        <FilesList path={path} sx={{ m: 2 }} />
      </Box>

      <Stack direction={'row'} sx={{ ml: 2 }} spacing={2}>
        <Tooltip title="Reload">
          <IconButton aria-label="reload" onClick={() => reloadProperties()}>
            <ReplayIcon />
          </IconButton>
        </Tooltip>
        <Button
          variant="outlined"
          color="success"
          onClick={openFinishDialog}
          sx={{ ml: 2 }}
        >
          Confirm Manualgrade
        </Button>
      </Stack>

      <AgreeDialog open={showDialog} {...dialogContent} />
    </Box>
  );
};

/*
import { ModalTitle } from '../../util/modal-title';
import { Box, Button, IconButton, Stack, Tooltip, Typography } from '@mui/material';
import * as React from 'react';
import { getProperties, updateSubmission } from '../../../services/submissions.service';
import { GradeBook } from '../../../services/gradebook';
import { createManualFeedback } from '../../../services/grading.service';
import { FilesList } from '../../util/file-list';
import { AgreeDialog } from '../../util/dialog';
import ReplayIcon from '@mui/icons-material/Replay';
import { enqueueSnackbar } from 'notistack';
import { openBrowser } from '../overview/util';
import { LoadingButton } from '@mui/lab';
export const ManualGrading = (props) => {
    const [gradeBook, setGradeBook] = React.useState(null);
    const [path, setPath] = React.useState(`edit/${props.lecture.code}/${props.assignment.id}/${props.submission.id}`);
    openBrowser(path);
    const [showDialog, setShowDialog] = React.useState(false);
    const [loading, setLoading] = React.useState(false);
    const [dialogContent, setDialogContent] = React.useState({
        title: '',
        message: '',
        handleAgree: null,
        handleDisagree: null
    });
    const openFinishDialog = () => {
        setDialogContent({
            title: 'Confirm Grading',
            message: 'Do you want to save the assignment grading?',
            handleAgree: finishGrading,
            handleDisagree: () => {
                setShowDialog(false);
            }
        });
        setShowDialog(true);
    };
    const finishGrading = () => {
        props.submission.manual_status = 'manually_graded';
        updateSubmission(props.lecture.id, props.assignment.id, props.submission.id, props.submission).then(response => {
            props.onClose();
            enqueueSnackbar('Successfully Graded Submission', {
                variant: 'success'
            });
        }, err => {
            enqueueSnackbar(err.message, {
                variant: 'error'
            });
        });
    };
    const reloadProperties = () => {
        getProperties(props.lecture.id, props.assignment.id, props.submission.id).then(properties => {
            const gradeBook = new GradeBook(properties);
            setGradeBook(gradeBook);
        }, err => {
            enqueueSnackbar(err.message, {
                variant: 'error'
            });
        });
    };
    const handlePullSubmission = async () => {
        await createManualFeedback(props.lecture.id, props.assignment.id, props.submission.id).then(() => {
            const editPath = `edit/${props.lecture.code}/${props.assignment.id}/${props.submission.id}`;
            setPath(editPath);
            openBrowser(editPath);
            enqueueSnackbar('Successfully Pulled Submission', {
                variant: 'success'
            });
        }, err => {
            enqueueSnackbar(err.message, {
                variant: 'error'
            });
        });
    };
    return (React.createElement(Box, { sx: { overflow: 'scroll', height: '100%' } },
        React.createElement(ModalTitle, { title: 'Manual Grading ' + props.assignment.id }),
        React.createElement(Box, { sx: { m: 2, mt: 5 } },
            React.createElement(Stack, { direction: "row", spacing: 2, sx: { ml: 2 } },
                React.createElement(Stack, { sx: { mt: 0.5 } },
                    React.createElement(Typography, { textAlign: "right", color: "text.secondary", sx: { fontSize: 12, height: 35 } }, "Username"),
                    React.createElement(Typography, { textAlign: "right", color: "text.secondary", sx: { fontSize: 12, height: 35 } }, "Lecture"),
                    React.createElement(Typography, { textAlign: "right", color: "text.secondary", sx: { fontSize: 12, height: 35 } }, "Assignment"),
                    React.createElement(Typography, { textAlign: "right", color: "text.secondary", sx: { fontSize: 12, height: 35 } }, "Points"),
                    React.createElement(Typography, { textAlign: "right", color: "text.secondary", sx: { fontSize: 12, height: 35 } }, "Extra Credit")),
                React.createElement(Stack, null,
                    React.createElement(Typography, { color: "text.primary", sx: { display: 'inline-block', fontSize: 16, height: 35 } }, props.username),
                    React.createElement(Typography, { color: "text.primary", sx: { display: 'inline-block', fontSize: 16, height: 35 } }, props.lecture.name),
                    React.createElement(Typography, { color: "text.primary", sx: { display: 'inline-block', fontSize: 16, height: 35 } },
                        props.assignment.name,
                        React.createElement(Typography, { color: "text.secondary", sx: {
                                display: 'inline-block',
                                fontSize: 14,
                                ml: 2,
                                height: 35
                            } }, props.assignment.type)),
                    React.createElement(Typography, { color: "text.primary", sx: { display: 'inline-block', fontSize: 16, height: 35 } }, gradeBook === null || gradeBook === void 0 ? void 0 :
                        gradeBook.getPoints(),
                        React.createElement(Typography, { color: "text.secondary", sx: { display: 'inline-block', fontSize: 14, ml: 0.25 } },
                            "/", gradeBook === null || gradeBook === void 0 ? void 0 :
                            gradeBook.getMaxPoints())),
                    React.createElement(Typography, { color: "text.primary", sx: { display: 'inline-block', fontSize: 16, height: 35 } }, gradeBook === null || gradeBook === void 0 ? void 0 : gradeBook.getExtraCredits())))),
        React.createElement(Typography, { sx: { m: 2, mb: 0 } }, "Submission Files"),
        React.createElement(Box, { sx: { overflowY: 'auto' } },
            React.createElement(FilesList, { path: path, sx: { m: 2 } })),
        React.createElement(Stack, { direction: 'row', sx: { ml: 2 }, spacing: 2 },
            React.createElement(Tooltip, { title: "Reload" },
                React.createElement(IconButton, { "aria-label": "reload", onClick: () => reloadProperties() },
                    React.createElement(ReplayIcon, null))),
            React.createElement(LoadingButton, { loading: loading, color: "primary", variant: "outlined", onClick: async () => {
                    setLoading(true);
                    await handlePullSubmission();
                    setLoading(false);
                } }, "Pull Edited Submission"),
            React.createElement(Button, { variant: "outlined", color: "success", onClick: openFinishDialog, sx: { ml: 2 } })),
        React.createElement(AgreeDialog, Object.assign({ open: showDialog }, dialogContent))));
};*/