import { SectionTitle } from '../../util/section-title';
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
import ReplayIcon from '@mui/icons-material/Replay';
import { enqueueSnackbar } from 'notistack';
import { openBrowser } from '../overview/util';
import { LoadingButton } from '@mui/lab';
import { lectureBasePath } from '../../../services/file.service';
import { Link, useOutletContext } from 'react-router-dom';
import Toolbar from '@mui/material/Toolbar';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import { showDialog } from '../../util/dialog-provider';

export const EditSubmission = () => {
  const {
    lecture,
    assignment,
    rows,
    setRows,
    manualGradeSubmission,
    setManualGradeSubmission
  } = useOutletContext() as {
    lecture: Lecture,
    assignment: Assignment,
    rows: Submission[],
    setRows: React.Dispatch<React.SetStateAction<Submission[]>>,
    manualGradeSubmission: Submission,
    setManualGradeSubmission: React.Dispatch<React.SetStateAction<Submission>>
  };
  const path = `${lectureBasePath}${lecture.code}/edit/${assignment.id}/${manualGradeSubmission.id}`;
  const submissionsLink = `/lecture/${lecture.id}/assignment/${assignment.id}/submissions`;

  const [submission, setSubmission] = React.useState(manualGradeSubmission);
  const [loading, setLoading] = React.useState(false);

  const pushEditedFiles = async () => {
    await pushSubmissionFiles(lecture, assignment, submission).then(
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
  };


  const handlePullEditedSubmission = async () => {
    await pullSubmissionFiles(lecture, assignment, submission).then(
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
    await createOrOverrideEditRepository(lecture.id, assignment.id, submission.id).then(
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
  };

  return (
    <Stack direction={'column'} sx={{ flex: '1 1 100%' }}>
      <Box sx={{ m: 2, mt: 5 }}>
        <Stack direction='row' spacing={2} sx={{ ml: 2 }}>
          <Stack sx={{ mt: 0.5 }}>
            <Typography
              textAlign='right'
              color='text.secondary'
              sx={{ fontSize: 12, height: 35 }}
            >
              Username
            </Typography>
            <Typography
              textAlign='right'
              color='text.secondary'
              sx={{ fontSize: 12, height: 35 }}
            >
              Assignment
            </Typography>
          </Stack>
          <Stack>
            <Typography
              color='text.primary'
              sx={{ display: 'inline-block', fontSize: 16, height: 35 }}
            >
              {submission.username}
            </Typography>

            <Typography
              color='text.primary'
              sx={{ display: 'inline-block', fontSize: 16, height: 35 }}
            >
              {assignment.name}
            </Typography>
          </Stack>
        </Stack>
      </Box>
      <Typography sx={{ m: 2, mb: 0 }}>Submission Files</Typography>
      <FilesList path={path} sx={{ m: 2 }} />

      <Stack direction={'row'} sx={{ ml: 2 }} spacing={2}>
        <LoadingButton
          loading={loading}
          color={submission.edited ? 'error' : 'primary'}
          variant='outlined'
          onClick={async () => {
            setLoading(true);
            await setEditRepository();
            setLoading(false);
          }}
        >
          {submission.edited ? 'Reset ' : 'Create '}
          Edit Repository
        </LoadingButton>

        <LoadingButton
          loading={loading}
          color='primary'
          variant='outlined'
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
          variant='outlined'
          color='success'
          disabled={!submission.edited}
          onClick={async () => {
            showDialog(
              'Edit Submission',
              'Do you want to push your submission changes?',
              async () => {
                await pushEditedFiles();
              }
            );
          }}
          sx={{ ml: 2 }}
        >
          Push Edited Submission
        </Button>
      </Stack>
      <Box sx={{ flex: '1 1 100%' }}></Box>
      <Toolbar>
        <Button variant='outlined' component={Link as any} to={submissionsLink}>Back</Button>
      </Toolbar>
    </Stack>
  );
};
