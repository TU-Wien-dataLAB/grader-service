import { SectionTitle } from '../../util/section-title';
import {
  Box,
  Button, Checkbox, FormControlLabel,
  IconButton,
  Stack, TextField,
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
import { autogradeSubmission, createManualFeedback, generateFeedback } from '../../../services/grading.service';
import { FilesList } from '../../util/file-list';
import ReplayIcon from '@mui/icons-material/Replay';
import { enqueueSnackbar } from 'notistack';
import { openBrowser } from '../overview/util';
import { LoadingButton } from '@mui/lab';
import { lectureBasePath } from '../../../services/file.service';
import { Link, useOutletContext } from 'react-router-dom';
import { utcToLocalFormat } from '../../../services/datetime.service';
import Toolbar from '@mui/material/Toolbar';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import { getAutogradeChip, getFeedbackChip, getManualChip } from './grading';
import { autogradeSubmissionsDialog, generateFeedbackDialog } from './table-toolbar';
import { showDialog } from '../../util/dialog-provider';


export const ManualGrading = () => {
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
  const submission = manualGradeSubmission;
  const manualPath = `${lectureBasePath}${lecture.code}/manualgrade/${assignment.id}/${submission.id}`;
  const rowIdx = rows.findIndex(s => s.id === submission.id);
  const submissionsLink = `/lecture/${lecture.id}/assignment/${assignment.id}/submissions`;

  const [submissionScaling, setSubmissionScaling] = React.useState(submission.score_scaling);

  const [gradeBook, setGradeBook] = React.useState(null);
  const [loading, setLoading] = React.useState(false);

  React.useEffect(() => {
    reloadProperties();
  }, []);

  const handleAutogradeSubmission = async () => {
    await autogradeSubmissionsDialog(async () => {
      try {
        await autogradeSubmission(lecture, assignment, submission);
        enqueueSnackbar('Autograding submission!', {
          variant: 'success'
        });
      } catch (err) {
        console.error(err);
        enqueueSnackbar('Error Autograding Submission', {
          variant: 'error'
        });
      }
    });
  };

  const handleGenerateFeedback = async () => {
    await generateFeedbackDialog(async () => {
      try {
        await generateFeedback(lecture.id, assignment.id, submission.id);
        enqueueSnackbar('Generating feedback for submission!', {
          variant: 'success'
        });
      } catch (err) {
        console.error(err);
        enqueueSnackbar('Error Generating Feedback', {
          variant: 'error'
        });
      }
    });
  };

  const openFinishDialog = () => {
    showDialog(
      'Confirm Grading',
      'Do you want to save the assignment grading?',
      finishGrading
    );
  };

  const finishGrading = () => {
    submission.manual_status = 'manually_graded';
    updateSubmission(
      lecture.id,
      assignment.id,
      submission.id,
      submission
    ).then(
      response => {
        enqueueSnackbar('Successfully Graded Submission', {
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

  const reloadProperties = () => {
    getProperties(
      lecture.id,
      assignment.id,
      submission.id
    ).then(properties => {
      const gradeBook = new GradeBook(properties);
      setGradeBook(gradeBook);
    });
  };

  const handlePullSubmission = async () => {
    createManualFeedback(lecture.id, assignment.id, submission.id).then(
      response => {
        openBrowser(manualPath);
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
              User
            </Typography>
            <Typography
              textAlign='right'
              color='text.secondary'
              sx={{ fontSize: 12, height: 35 }}
            >
              Submitted at
            </Typography>
            <Typography
              textAlign='right'
              color='text.secondary'
              sx={{ fontSize: 12, height: 35 }}
            >
              Points
            </Typography>
            <Typography
              textAlign='right'
              color='text.secondary'
              sx={{ fontSize: 12, height: 35 }}
            >
              Extra Credit
            </Typography>
            <Typography
              textAlign='right'
              color='text.secondary'
              sx={{ fontSize: 12, height: 75 }}
            >
              Score Scaling
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
              {utcToLocalFormat(submission.submitted_at)}
            </Typography>
            <Typography
              color='text.primary'
              sx={{ display: 'inline-block', fontSize: 16, height: 35 }}
            >
              {gradeBook?.getPoints()}
              <Typography
                color='text.secondary'
                sx={{ display: 'inline-block', fontSize: 14, ml: 0.25 }}
              >
                /{gradeBook?.getMaxPoints()}
              </Typography>
            </Typography>
            <Typography
              color='text.primary'
              sx={{ display: 'inline-block', fontSize: 16, height: 35 }}
            >
              {gradeBook?.getExtraCredits()}
            </Typography>
            <Box sx={{ height: 75 }}>
              <form onSubmit={(event) => {
                const s = submission;
                s.score_scaling = submissionScaling;
                updateSubmission(lecture.id, assignment.id, submission.id, s).then(() => {
                  enqueueSnackbar('Updated submission scaling!', { variant: 'success' });
                });
                event.preventDefault();
              }}>
                <Stack direction={'row'} spacing={2}>
                  <TextField id={'scaling'} label={'Scaling'} value={submissionScaling} size={'small'}
                             type={'number'} inputProps={{ maxLength: 4, step: '0.01', min: 0.0, max: 1.0 }}
                             onChange={e => setSubmissionScaling(+e.target.value)} />
                  <Button color='primary' variant='contained' type='submit'>
                    Update
                  </Button>
                </Stack>
              </form>

            </Box>
          </Stack>
        </Stack>
        <Stack direction={'row'} spacing={2}>
          <Box sx={{ flex: 'auto' }}>
            <Typography color='text.primary' sx={{ fontSize: 14 }}>Autograde
              Status: {getAutogradeChip(submission)}</Typography>
          </Box>
          <Box sx={{ flex: 'auto' }}>
            <Typography color='text.primary' sx={{ fontSize: 14 }}>Manualgrade
              Status: {getManualChip(submission)}</Typography>
          </Box>
          <Box sx={{ flex: 'auto' }}>
            <Typography color='text.primary' sx={{ fontSize: 14 }}>Feedback: {getFeedbackChip(submission)}</Typography>
          </Box>
        </Stack>
      </Box>
      <Typography sx={{ m: 2, mb: 0 }}>Submission Files</Typography>
      <FilesList path={manualPath} sx={{ m: 2 }} />

      <Stack direction={'row'} sx={{ ml: 2, mr: 2 }} spacing={2}>
        <Tooltip title='Reload'>
          <IconButton aria-label='reload' onClick={() => reloadProperties()}>
            <ReplayIcon />
          </IconButton>
        </Tooltip>

        <LoadingButton
          size={'small'}
          loading={loading}
          disabled={submission.auto_status !== 'automatically_graded'}
          color='primary'
          variant='outlined'
          onClick={async () => {
            setLoading(true);
            await handlePullSubmission();
            setLoading(false);
          }}
          sx={{ whiteSpace: 'nowrap', minWidth: 'auto' }}
        >
          Pull Submission
        </LoadingButton>

        <Button
          size={'small'}
          variant='outlined'
          color='success'
          onClick={openFinishDialog}
          sx={{ whiteSpace: 'nowrap', minWidth: 'auto' }}
        >
          Finish Manual Grading
        </Button>
        <Button
          size={'small'}
          variant='outlined'
          color='success'
          component={Link as any} to={submissionsLink + '/edit'}
          sx={{ whiteSpace: 'nowrap', minWidth: 'auto' }}
        >
          Edit Submission
        </Button>
        <Box sx={{ flex: '1 1 100%' }}></Box>
        <Button
          size={'small'}
          variant='outlined'
          color='primary'
          onClick={handleAutogradeSubmission}
          sx={{ whiteSpace: 'nowrap', minWidth: 'auto' }}
        >
          Autograde
        </Button>
        <Button
          size={'small'}
          variant='outlined'
          color='primary'
          onClick={handleGenerateFeedback}
          sx={{ whiteSpace: 'nowrap', minWidth: 'auto' }}
        >
          Generate Feedback
        </Button>
      </Stack>
      <Box sx={{ flex: '1 1 100%' }}></Box>
      <Toolbar>
        <Button variant='outlined' component={Link as any} to={submissionsLink}>Back</Button>
        <Box sx={{ flex: '1 1 100%' }}></Box>
        <IconButton aria-label='previous' disabled={rowIdx === 0} color='primary' onClick={() => {
          const prevSub = rows[rowIdx - 1];
          setManualGradeSubmission(prevSub);
        }}>
          <ArrowBackIcon />
        </IconButton>
        <IconButton aria-label='next' disabled={rowIdx === rows.length - 1} color='primary' onClick={() => {
          const nextSub = rows[rowIdx + 1];
          setManualGradeSubmission(nextSub);
        }}>
          <ArrowForwardIcon />
        </IconButton>
      </Toolbar>
    </Stack>
  );
};