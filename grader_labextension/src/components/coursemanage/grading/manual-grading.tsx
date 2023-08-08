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
  getProperties,
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
import { lectureBasePath } from '../../../services/file.service';
import { useOutletContext } from 'react-router-dom';
import { utcToLocalFormat } from '../../../services/datetime.service';


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
  const rowIdx = rows.find(s => s.id = submission.id);

  const [gradeBook, setGradeBook] = React.useState(null);
  const [showDialog, setShowDialog] = React.useState(false);
  const [loading, setLoading] = React.useState(false);
  const [dialogContent, setDialogContent] = React.useState({
    title: '',
    message: '',
    handleAgree: null,
    handleDisagree: null
  });

  React.useEffect(() => {
    reloadProperties();
  }, []);

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
    <Box sx={{ height: '100%' }}>
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
          </Stack>
        </Stack>
      </Box>
      <Typography sx={{ m: 2, mb: 0 }}>Submission Files</Typography>
      <Box sx={{ overflowY: 'auto' }}>
        <FilesList path={manualPath} sx={{ m: 2 }} />
      </Box>

      <Stack direction={'row'} sx={{ ml: 2 }} spacing={2}>
        <Tooltip title='Reload'>
          <IconButton aria-label='reload' onClick={() => reloadProperties()}>
            <ReplayIcon />
          </IconButton>
        </Tooltip>

        <LoadingButton
          loading={loading}
          color='primary'
          variant='outlined'
          onClick={async () => {
            setLoading(true);
            await handlePullSubmission();
            setLoading(false);
          }}
        >
          Pull Submission
        </LoadingButton>

        <Button
          variant='outlined'
          color='success'
          onClick={openFinishDialog}
          sx={{ ml: 2 }}
        >
          Finish Manual Grading
        </Button>
      </Stack>

      <AgreeDialog open={showDialog} {...dialogContent} />
    </Box>
  );
};