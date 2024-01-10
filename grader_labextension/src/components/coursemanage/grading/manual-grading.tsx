import { SectionTitle } from '../../util/section-title';
import {
  Alert,
  AlertTitle,
  Box,
  Button, Checkbox, FormControlLabel,
  IconButton,
  Modal,
  Stack, TextField,
  Tooltip,
  Typography
} from '@mui/material';
import * as React from 'react';
import { Lecture } from '../../../model/lecture';
import { Assignment } from '../../../model/assignment';
import { Submission } from '../../../model/submission';
import {
  getProperties, getSubmission,
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
import InfoIcon from '@mui/icons-material/Info';

const style = {
  position: 'absolute' as 'absolute',
  top: '50%',
  left: '50%',
  transform: 'translate(-50%, -50%)',
  width: '80%',
  bgcolor: 'background.paper',
  boxShadow: 3,
  pt: 2,
  px: 4,
  pb: 3
  
};

const InfoModal = () =>{
  const [open, setOpen] = React.useState(false);
  const handleOpen = () => {
    setOpen(true);
  };
  const handleClose = () => {
    setOpen(false);
  };
  return (
    <React.Fragment>
      <IconButton color="primary" onClick={handleOpen} sx={{mr: 2}}>
          <InfoIcon/>
      </IconButton>
      <Modal
        open={open}
        onClose={handleClose}
      >
        <Box sx={{...style }}>
          <h2>Manual Grading Information</h2>
          <Alert severity="info" sx={{ m: 2 }}>
            <AlertTitle>Info</AlertTitle>
            If you want to manually grade an assignment, make sure to follow these steps: <br /><br />
            1. &ensp; In order to grade a submission manually, the submission must first be auto-graded. This sets meta data for manual grading. However, we're actively working towards enabling direct manual grading without the necessity of auto-grading in the future.<br />
            2. &ensp; Once the meta data was set for submission, you can pull the submission.<br />
            3. &ensp; From file list access submission files and grade them manually.<br />
            4. &ensp; After you've completed the grading of the submission, click "FINISH MANUAL GRADING." This action will save the grading and determine the points that the student receives for their submission.
          </Alert>
          <Button onClick={handleClose}>Close</Button>
        </Box>
      </Modal>
    </React.Fragment>
  );
}

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
  const [submission, setSubmission] = React.useState(manualGradeSubmission);
  const mPath = `${lectureBasePath}${lecture.code}/manualgrade/${assignment.id}/${submission.id}`;
  const rowIdx = rows.findIndex(s => s.id === submission.id);
  const submissionsLink = `/lecture/${lecture.id}/assignment/${assignment.id}/submissions`;

  const [submissionScaling, setSubmissionScaling] = React.useState(submission.score_scaling);
  const [manualPath, setManualPath] = React.useState(mPath);
  const [gradeBook, setGradeBook] = React.useState(null);
  const [loading, setLoading] = React.useState(false);

  React.useEffect(() => {
    reloadProperties();
  }, []);

  const reloadManualPath = () => {
    setManualPath(mPath);
  };

  const reloadProperties = () => {
    getProperties(
      lecture.id,
      assignment.id,
      submission.id,
      true
    ).then(properties => {
      const gradeBook = new GradeBook(properties);
      setGradeBook(gradeBook);
    });
  };

  const reloadSubmission = () => {
    getSubmission(lecture.id, assignment.id, submission.id, true).then(s => setSubmission(s));
  };

  const reload = () => {
    reloadSubmission();
    reloadProperties();
    reloadManualPath();
  };

  const handleAutogradeSubmission = async () => {
    await autogradeSubmissionsDialog(async () => {
      try {
        await autogradeSubmission(lecture, assignment, submission);
        enqueueSnackbar('Autograding submission!', {
          variant: 'success'
        });
        reload();
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
        reload();
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
        reload();
      },
      err => {
        enqueueSnackbar(err.message, {
          variant: 'error'
        });
        reload();
      }
    );
  };

  const handlePullSubmission = async () => {
    createManualFeedback(lecture.id, assignment.id, submission.id).then(
      response => {
        openBrowser(manualPath);
        enqueueSnackbar('Successfully Pulled Submission', {
          variant: 'success'
        });
        reload();
      },
      err => {
        enqueueSnackbar(err.message, {
          variant: 'error'
        });
      }
    );
  };

  return (
    <Box sx={{ overflow: 'auto' }}>
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

      <Stack direction={'row'} justifyContent={'space-between'}>
        <Typography sx={{ m: 2, mb: 0 }}>Submission Files</Typography>
        <InfoModal/>
      </Stack>
      

      <FilesList path={manualPath} sx={{ m: 2 }} />

      <Stack direction={'row'} sx={{ ml: 2, mr: 2 }} spacing={2}>
        <Tooltip title='Reload'>
          <IconButton aria-label='reload' onClick={() => reload()}>
            <ReplayIcon />
          </IconButton>
        </Tooltip>
        
        {submission.auto_status !== 'automatically_graded' ?
        <Tooltip title="Assinment is not auto-graded. To pull submission and finish manual grading, make sure to first autograde it.">
              <Button
                size={'small'}
                variant='outlined'
                color='primary'
                onClick={handleAutogradeSubmission}
                sx={{ whiteSpace: 'nowrap', minWidth: 'auto' }}
              >
                Autograde
              </Button>
        </Tooltip>
     
        : null}
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
          disabled={submission.auto_status !== 'automatically_graded'}
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
        {submission.auto_status === 'automatically_graded' ?
              <Button
              size={'small'}
              variant='outlined'
              color='primary'
              onClick={handleAutogradeSubmission}
              sx={{ whiteSpace: 'nowrap', minWidth: 'auto' }}
              >
              Autograde
              </Button>
        : null}
        
        {submission.auto_status === 'automatically_graded' ?
        <Button
          size={'small'}
          variant='outlined'
          color='primary'
          onClick={handleGenerateFeedback}
          sx={{ whiteSpace: 'nowrap', minWidth: 'auto' }}
        >
          Generate Feedback
        </Button>
        : null}
      </Stack>
      <Box sx={{ flex: '1 1 100%', mt: 3 }}></Box>
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
    </Box>
  );
};