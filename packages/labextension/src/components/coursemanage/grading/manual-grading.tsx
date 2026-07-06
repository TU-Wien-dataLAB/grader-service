import {
  Alert,
  AlertTitle,
  Box,
  Button,
  IconButton,
  Modal,
  Stack,
  TextField,
  Tooltip,
  Typography
} from '@mui/material';
import * as React from 'react';
import { Lecture } from '../../../model/lecture';
import { Assignment } from '../../../model/assignment';
import { Submission } from '../../../model/submission';
import {
  getProperties,
  getSubmission,
  updateSubmission
} from '../../../services/submissions.service';
import { GradeBook } from '../../../services/gradebook';
import {
  autogradeSubmission,
  createManualFeedback,
  generateFeedback
} from '../../../services/grading.service';
import { FilesList } from '../../util/file-list';
import { enqueueSnackbar } from 'notistack';
import { openBrowser } from '../overview/util';
import { getFiles, lectureBasePath } from '../../../services/file.service';
import { Link, useOutletContext } from 'react-router-dom';
import { utcToLocalFormat } from '../../../services/datetime.service';
import Toolbar from '@mui/material/Toolbar';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import { getAutogradeChip, getFeedbackChip, getManualChip } from './grading';
import {
  autogradeSubmissionsDialog,
  generateFeedbackDialog
} from './table-toolbar';
import { showDialog } from '../../util/dialog-provider';
import InfoIcon from '@mui/icons-material/Info';
import { GraderLoadingButton } from '../../util/loading-button';
import { useQuery } from '@tanstack/react-query';
import { queryClient } from '../../../widgets/assignmentmanage';
import { ManualStatus } from '../../../model/manualStatus';
import { FeedbackStatus } from '../../../model/feedbackStatus';
import { AutoStatus } from '../../../model/autoStatus';
import { AssignmentSettings } from '../../../model/assignmentSettings';

const style = {
  position: 'absolute' as const,
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

const InfoModal = () => {
  const [open, setOpen] = React.useState(false);
  const handleOpen = () => {
    setOpen(true);
  };
  const handleClose = () => {
    setOpen(false);
  };
  return (
    <React.Fragment>
      <IconButton color="primary" onClick={handleOpen} sx={{ mr: 2 }}>
        <InfoIcon />
      </IconButton>
      <Modal open={open} onClose={handleClose}>
        <Box sx={{ ...style }}>
          <h2>Manual Grading Information</h2>
          <Alert severity="info" sx={{ m: 2 }}>
            <AlertTitle>Info</AlertTitle>
            If you want to manually grade a submission, please follow these
            steps: <br />
            <br />
            1. &ensp; Pull the submission.
            <br />
            2. &ensp; Access the submission files from the file list and grade
            them manually.
            <br />
            3. &ensp; After you've completed the grading of the submission and
            saved revised notebook, click button "FINISH MANUAL GRADING". This
            action will save the grading and determine the points that the
            student receives for their submission.
          </Alert>
          <Button onClick={handleClose}>Close</Button>
        </Box>
      </Modal>
    </React.Fragment>
  );
};

export const ManualGrading = () => {
  const {
    lecture,
    assignment,
    rows,
    setRows: _setRows, //not used
    manualGradeSubmission,
    setManualGradeSubmission
  } = useOutletContext() as {
    lecture: Lecture;
    assignment: Assignment;
    rows: Submission[];
    setRows: React.Dispatch<React.SetStateAction<Submission[]>>;
    manualGradeSubmission: Submission;
    setManualGradeSubmission: React.Dispatch<React.SetStateAction<Submission>>;
  };

  const rowIdx = rows.findIndex(s => s.id === manualGradeSubmission.id);
  const submissionsLink = `/lecture/${lecture.id}/assignment/${assignment.id}/submissions`;

  const {
    data: submission = manualGradeSubmission,
    refetch: refetchSubmission
  } = useQuery<Submission>({
    queryKey: [
      'submission',
      lecture.id,
      assignment.id,
      manualGradeSubmission.id
    ],
    queryFn: () =>
      getSubmission(lecture.id, assignment.id, manualGradeSubmission.id, true)
  });

  const [submissionScaling, setSubmissionScaling] = React.useState(
    submission.score_scaling
  );
  const manualPath = `${lectureBasePath}${lecture.code}/manualgrade/${assignment.id}/${submission.id}`;

  const { data: gradeBook, refetch: refetchGradeBook } = useQuery({
    queryKey: ['gradeBook', submission.id],
    queryFn: () =>
      getProperties(lecture.id, assignment.id, submission.id, true).then(
        properties => new GradeBook(properties)
      ),
    enabled: !!submission
  });

  // state to store files for manual grading
  const [manualFiles, setManualFiles] = React.useState<any[]>([]);

  React.useEffect(() => {
    refetchSubmission().then(async response => {
      setSubmissionScaling(response.data.score_scaling);
      await refetchGradeBook();

      const manualPath = `${lectureBasePath}${lecture.code}/manualgrade/${assignment.id}/${manualGradeSubmission.id}`;
      const files = await getFiles(manualPath);
      setManualFiles(files);

      if (files.length === 0) {
        openBrowser(
          `${lectureBasePath}${lecture.code}/source/${assignment.id}`
        );
      } else {
        openBrowser(manualPath);
      }
    });
  }, [manualGradeSubmission.id]);

  const isAutogradingDisabled = () => {
    return assignment.settings?.autograde_type ===
      AssignmentSettings.AutogradeTypeEnum.Unassisted
      ? false
      : submission.auto_status !== AutoStatus.AutomaticallyGraded;
  };

  const showFeedbackButton = () => {
    if (
      assignment.settings?.autograde_type ===
      AssignmentSettings.AutogradeTypeEnum.Unassisted
    ) {
      // show the button if the submission has either been
      // manually or automatically graded
      return (
        submission.manual_status === ManualStatus.ManuallyGraded ||
        submission.auto_status === AutoStatus.AutomaticallyGraded
      );
    } else {
      return submission.auto_status === AutoStatus.AutomaticallyGraded;
    }
  };
  const handleAutogradeSubmission = async () => {
    await autogradeSubmissionsDialog(async () => {
      try {
        await autogradeSubmission(lecture, assignment, submission).then(() => {
          refetchSubmission();
          queryClient.invalidateQueries({
            queryKey: [
              'submissionLogs',
              lecture.id,
              assignment.id,
              submission.id
            ]
          });
        });
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
        await generateFeedback(lecture, assignment, submission).then(() => {
          refetchSubmission().then(() => refetchGradeBook());
        });
        enqueueSnackbar('Generating feedback for submission!', {
          variant: 'success'
        });
        await queryClient.invalidateQueries({
          queryKey: ['submissionsAssignmentStudent']
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
    submission.manual_status = ManualStatus.ManuallyGraded;
    if (submission.feedback_status === FeedbackStatus.Generated) {
      submission.feedback_status = FeedbackStatus.FeedbackOutdated;
    }
    updateSubmission(lecture.id, assignment.id, submission.id, submission).then(
      response => {
        refetchSubmission().then(() => refetchGradeBook());
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

  const handlePullSubmission = async () => {
    createManualFeedback(lecture.id, assignment.id, submission.id).then(
      async response => {
        const files = await getFiles(manualPath);
        setManualFiles(files);
        openBrowser(manualPath);
        refetchGradeBook();
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

  const handleNavigation = direction => {
    const currentIndex = rows.findIndex(s => s.id === submission.id);
    const newIndex = direction === 'next' ? currentIndex + 1 : currentIndex - 1;

    if (newIndex >= 0 && newIndex < rows.length) {
      const newSubmission = rows[newIndex];
      setManualGradeSubmission(newSubmission);
    }
  };

  return (
    <Box sx={{ overflow: 'auto' }}>
      <Stack direction={'column'} sx={{ flex: '1 1 100%' }}>
        <Box sx={{ m: 2, mt: 5 }}>
          {gradeBook?.missingGradeCells().length > 0 ? (
            <Alert sx={{ mb: 2 }} severity="warning">
              Grading cells were deleted from submission!
            </Alert>
          ) : null}
          <Stack direction="row" spacing={2} sx={{ ml: 2 }}>
            <Stack sx={{ mt: 0.5 }}>
              <Typography
                textAlign="right"
                color="text.secondary"
                sx={{ fontSize: 12, height: 35 }}
              >
                User
              </Typography>
              <Typography
                textAlign="right"
                color="text.secondary"
                sx={{ fontSize: 12, height: 35 }}
              >
                Submitted at
              </Typography>
              <Typography
                textAlign="right"
                color="text.secondary"
                sx={{ fontSize: 12, height: 35 }}
              >
                Achieved Points
              </Typography>
              <Typography
                textAlign="right"
                color="text.secondary"
                sx={{ fontSize: 12, height: 35 }}
              >
                Extra Credit
              </Typography>
              <Typography
                textAlign="right"
                color="text.secondary"
                sx={{ fontSize: 12, height: 35 }}
              >
                Final Score
              </Typography>
              <Typography
                textAlign="right"
                color="text.secondary"
                sx={{ fontSize: 12, height: 75 }}
              >
                Score Scaling
              </Typography>
            </Stack>
            <Stack>
              <Typography
                color="text.primary"
                sx={{ display: 'inline-block', fontSize: 16, height: 35 }}
              >
                {submission.user_display_name}
              </Typography>
              <Typography
                color="text.primary"
                sx={{ display: 'inline-block', fontSize: 16, height: 35 }}
              >
                {utcToLocalFormat(submission.submitted_at)}
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
              <Typography
                color="text.primary"
                sx={{ display: 'inline-block', fontSize: 16, height: 35 }}
              >
                {submission.score}
              </Typography>
              <Box sx={{ height: 75 }}>
                <form
                  onSubmit={event => {
                    const s = submission;
                    s.score_scaling = submissionScaling;
                    updateSubmission(
                      lecture.id,
                      assignment.id,
                      submission.id,
                      s
                    ).then(() => {
                      enqueueSnackbar('Updated submission scaling!', {
                        variant: 'success'
                      });
                      refetchSubmission();
                    });
                    event.preventDefault();
                  }}
                >
                  <Stack direction={'row'} spacing={2}>
                    <TextField
                      id={'scaling'}
                      label={'Scaling'}
                      value={submissionScaling}
                      size={'small'}
                      type={'number'}
                      slotProps={{
                        htmlInput: {
                          maxLength: 4,
                          step: '0.01',
                          min: 0.0,
                          max: 1.0
                        }
                      }}
                      onChange={e => setSubmissionScaling(+e.target.value)}
                    />
                    <Button color="primary" variant="contained" type="submit">
                      Update
                    </Button>
                  </Stack>
                </form>
              </Box>
            </Stack>
          </Stack>
          <Stack direction={'row'} spacing={2}>
            <Box sx={{ flex: 'auto' }}>
              <Typography color="text.primary" sx={{ fontSize: 14 }}>
                Autograde Status: {getAutogradeChip(submission)}
              </Typography>
            </Box>
            <Box sx={{ flex: 'auto' }}>
              <Typography color="text.primary" sx={{ fontSize: 14 }}>
                Manualgrade Status: {getManualChip(submission)}
              </Typography>
            </Box>
            <Box sx={{ flex: 'auto' }}>
              <Typography color="text.primary" sx={{ fontSize: 14 }}>
                Feedback: {getFeedbackChip(submission)}
              </Typography>
            </Box>
          </Stack>
        </Box>

        <Stack direction={'row'} justifyContent={'space-between'}>
          <Typography sx={{ m: 2, mb: 0 }}>Submission Files</Typography>
          <InfoModal />
        </Stack>

        <FilesList
          files={manualFiles}
          sx={{ m: 2 }}
          lecture={lecture}
          assignment={assignment}
          checkboxes={false}
        />

        <Stack direction={'row'} sx={{ ml: 2, mr: 2 }} spacing={2}>
          {submission.auto_status !== AutoStatus.AutomaticallyGraded ? (
            <Tooltip title="Assinment is not auto-graded. To pull submission and finish manual grading, make sure to first autograde it.">
              <Button
                variant="outlined"
                color="primary"
                onClick={handleAutogradeSubmission}
                sx={{ whiteSpace: 'nowrap', minWidth: 'auto' }}
              >
                Autograde
              </Button>
            </Tooltip>
          ) : null}
          <GraderLoadingButton
            disabled={isAutogradingDisabled()}
            color="primary"
            variant="outlined"
            onClick={handlePullSubmission}
            sx={{ whiteSpace: 'nowrap', minWidth: 'auto' }}
          >
            Pull Submission
          </GraderLoadingButton>

          <Button
            variant="outlined"
            color="success"
            disabled={isAutogradingDisabled()}
            onClick={openFinishDialog}
            sx={{ whiteSpace: 'nowrap', minWidth: 'auto' }}
          >
            Finish Manual Grading
          </Button>
          <Tooltip title="Edit Submission allows you to revise a student's submission. This may be useful if the student made a minor mistake that significantly affected their score or caused autograding to fail.">
            <Button
              variant="outlined"
              color="success"
              component={Link as any}
              to={submissionsLink + '/edit'}
              sx={{ whiteSpace: 'nowrap', minWidth: 'auto' }}
            >
              Edit Submission
            </Button>
          </Tooltip>
          <Box sx={{ flex: '1 1 100%' }}></Box>
          {submission.auto_status === AutoStatus.AutomaticallyGraded ? (
            <Button
              variant="outlined"
              color="primary"
              onClick={handleAutogradeSubmission}
              sx={{ whiteSpace: 'nowrap', minWidth: 'auto' }}
            >
              Autograde
            </Button>
          ) : null}

          {showFeedbackButton() ? (
            <Button
              variant="outlined"
              color="primary"
              onClick={handleGenerateFeedback}
              sx={{ whiteSpace: 'nowrap', minWidth: 'auto' }}
            >
              Generate Feedback
            </Button>
          ) : null}
        </Stack>
        <Box sx={{ flex: '1 1 100%', mt: 3 }}></Box>
        <Toolbar>
          <Button
            variant="outlined"
            component={Link as any}
            to={submissionsLink}
          >
            Back
          </Button>
          <Box sx={{ flex: '1 1 100%' }}></Box>
          <IconButton
            aria-label="previous"
            disabled={rowIdx === 0}
            color="primary"
            onClick={() => handleNavigation('previous')}
          >
            <ArrowBackIcon />
          </IconButton>
          <IconButton
            aria-label="next"
            disabled={rowIdx === rows.length - 1}
            color="primary"
            onClick={() => handleNavigation('next')}
          >
            <ArrowForwardIcon />
          </IconButton>
        </Toolbar>
      </Stack>
    </Box>
  );
};
