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
  createOrOverrideEditRepository,
  getProperties,
  pullSubmissionFiles,
  pushSubmissionFiles,
  updateSubmission
} from '../../../services/submissions.service';
import { GradeBook } from '../../../services/gradebook';
import { createManualFeedback } from '../../../services/grading.service';
import { FilesList } from '../../util/file-list';
import { AgreeDialog } from '../../util/dialog';
import ReplayIcon from '@mui/icons-material/Replay';
import { enqueueSnackbar } from 'notistack';
import { openBrowser } from '../overview/util';
import { LoadingButton } from '@mui/lab';
import { pullAssignment, pushAssignment } from '../../../services/assignments.service';
import { sub } from 'date-fns';

export interface IEditSubmissionProps {
  lecture: Lecture;
  assignment: Assignment;
  submission: Submission;
  username: string;
  onClose: () => void;
}

export const EditSubmission = (props: IEditSubmissionProps) => {

  const [path, setPath] = React.useState(
    `edit/${props.lecture.code}/${props.assignment.id}/${props.submission.id}`
  );

  const [submission, setSubmission] = React.useState(props.submission);

  const [showDialog, setShowDialog] = React.useState(false);
  const [loading, setLoading] = React.useState(false);
  const [dialogContent, setDialogContent] = React.useState({
    title: '',
    message: '',
    handleAgree: null,
    handleDisagree: null
  });

  const openFinishEditing = () => {
    setDialogContent({
      title: 'Edit Submission',
      message: 'Do you want to push your submission changes?',
      handleAgree: async () => { 
        await pushEditedFiles();
      },
      handleDisagree: () => {
        setShowDialog(false);
      }
    });
    setShowDialog(true);
  };

  const pushEditedFiles = async () => {
    await pushSubmissionFiles(props.lecture, props.assignment, submission).then(
      response => {
        enqueueSnackbar('Successfully Pushed Edited Submission', {
          variant: 'success'
        });
      },
      err => {
        enqueueSnackbar(err.message, {
          variant: 'error'
        });
      }
    );
    props.onClose();
  };


  const handlePullEditedSubmission = async () => {
    await pullSubmissionFiles(props.lecture, props.assignment, submission).then(
      response => {
        openBrowser(path);
        enqueueSnackbar('Successfully Pulled Submission', {
          variant: 'success'
        });
      },
      err => {
        enqueueSnackbar(err.message, {
          variant: 'error'
        });
      }
    );
  };

  const setEditRepository = async () => {
    await createOrOverrideEditRepository(props.lecture.id, props.assignment.id, submission.id).then(
      response => {
        enqueueSnackbar('Successfully Created Edit Repository', {
          variant: 'success'
        });
        setSubmission(response);
      },
      err => {
        enqueueSnackbar(err.message, {
          variant: 'error'
        });
      }
    );
  }

  return (
    <Box sx={{ overflow: 'scroll', height: '100%' }}>
      <ModalTitle title={'Manual Grading ' + props.assignment.id} />
      <Box sx={{ m: 2, mt: 5 }}>
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
              Assignment
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
              {props.assignment.name}
            </Typography>
          </Stack>
        </Stack>
      </Box>
      <Typography sx={{ m: 2, mb: 0 }}>Submission Files</Typography>
      <Box sx={{ overflowY: 'auto' }}>
        <FilesList path={path} sx={{ m: 2 }} />
      </Box>

      <Stack direction={'row'} sx={{ ml: 2 }} spacing={2}>
      <LoadingButton
          loading={loading}
          color={submission.edited ? "error" : "primary"}
          variant="outlined"
          onClick={async () => {
            setLoading(true);
            await setEditRepository();
            setLoading(false);
          }}
        >
          {submission.edited ? "Reset " : "Create " }
          Edit Repository
        </LoadingButton>

        <LoadingButton
          loading={loading}
          color="primary"
          variant="outlined"
          disabled={!submission.edited}
          onClick={async () => {
            setLoading(true);
            await handlePullEditedSubmission();
            setLoading(false);
          }}
        >
          Pull Submission
        </LoadingButton>

        <Button
          variant="outlined"
          color="success"
          disabled={!submission.edited}
          onClick={async () => {
            setLoading(true);
            await openFinishEditing();
            setLoading(false);
          }}
          sx={{ ml: 2 }}
        >
            Push Edited Submission
        </Button>
      </Stack>

      <AgreeDialog open={showDialog} {...dialogContent} />
    </Box>
  );
}
