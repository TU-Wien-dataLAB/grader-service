import { Box, Button, Stack, Typography } from '@mui/material';
import * as React from 'react';
import { Lecture } from '../../../model/lecture';
import { Assignment } from '../../../model/assignment';
import { Submission } from '../../../model/submission';
import {
  createOrOverrideEditRepository,
  getSubmission,
  pullSubmissionFiles,
  pushSubmissionFiles
} from '../../../services/submissions.service';
import { FilesList } from '../../util/file-list';
import { enqueueSnackbar } from 'notistack';
import { openBrowser } from '../overview/util';
import { lectureBasePath, getFiles } from '../../../services/file.service';
import { useNavigate, useOutletContext } from 'react-router-dom';
import Toolbar from '@mui/material/Toolbar';
import { showDialog } from '../../util/dialog-provider';
import { GraderLoadingButton } from '../../util/loading-button';
import { useQuery } from '@tanstack/react-query';
import { SubmissionLogs } from '../../util/submission-logs';
import { Contents } from '@jupyterlab/services';
import { GlobalObjects } from '../../..';

export const EditSubmission = () => {
  const navigate = useNavigate();

  const { lecture, assignment, manualGradeSubmission } = useOutletContext() as {
    lecture: Lecture;
    assignment: Assignment;
    manualGradeSubmission: Submission;
  };

  const path = `${lectureBasePath}${lecture.code}/edit/${assignment.id}/${manualGradeSubmission.id}`;
  openBrowser(path);

  const { data: submission, refetch: refetchSubmission } = useQuery({
    queryKey: [
      'submission',
      lecture.id,
      assignment.id,
      manualGradeSubmission.id
    ],
    queryFn: () =>
      getSubmission(lecture.id, assignment.id, manualGradeSubmission.id, true)
  });

  const { data: files = [], refetch: refetchFiles } = useQuery({
    queryKey: ['submissionFiles', path],
    queryFn: () => getFiles(path),
    enabled: !!path
  });

  React.useEffect(() => {
    // Watch for file changes in the JupyterLab file browser
    GlobalObjects.docManager.services.contents.fileChanged.connect(
      (sender: Contents.IManager, change: Contents.IChangedArgs) => {
        const { oldValue, newValue } = change;
        if (
          (newValue && !newValue.path.includes(path)) ||
          (oldValue && !oldValue.path.includes(path))
        ) {
          return;
        }
        refetchFiles();
      }
    );
  });

  const [showLogs, setShowLogs] = React.useState(false);

  const reloadSubmission = async () => {
    await refetchSubmission();
    refetchFiles();
  };

  const pushEditedFiles = async () => {
    await pushSubmissionFiles(lecture, assignment, submission).then(
      () => {
        enqueueSnackbar('Successfully Pushed Edited Submission', {
          variant: 'success'
        });
        refetchFiles();
      },
      err => {
        enqueueSnackbar(err.message, { variant: 'error' });
      }
    );
  };

  const handlePullEditedSubmission = async () => {
    await pullSubmissionFiles(lecture, assignment, submission).then(
      () => {
        openBrowser(path);
        enqueueSnackbar('Successfully Pulled Submission', {
          variant: 'success'
        });
        refetchFiles();
      },
      err => {
        enqueueSnackbar(err.message, { variant: 'error' });
      }
    );
  };

  const setEditRepository = async () => {
    await createOrOverrideEditRepository(
      lecture.id,
      assignment.id,
      submission.id
    ).then(
      () => {
        enqueueSnackbar('Successfully Created Edit Repository', {
          variant: 'success'
        });
        reloadSubmission();
      },
      err => {
        enqueueSnackbar(err.message, { variant: 'error' });
      }
    );
  };

  return (
    <Stack direction="column" sx={{ flex: '1 1 100%', overflow: 'auto' }}>
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
            <Typography color="text.primary" sx={{ fontSize: 16, height: 35 }}>
              {submission?.user_display_name}
            </Typography>
            <Typography color="text.primary" sx={{ fontSize: 16, height: 35 }}>
              {assignment.name}
            </Typography>
          </Stack>
        </Stack>
      </Box>

      <Stack direction="row" justifyContent="space-between">
        <Typography sx={{ m: 2, mb: 0 }}>Submission Files</Typography>
        <Button
          sx={{ mr: 2 }}
          variant="outlined"
          size="small"
          onClick={() => setShowLogs(true)}
        >
          Show Logs
        </Button>
      </Stack>

      <FilesList
        files={files}
        sx={{ m: 2 }}
        lecture={lecture}
        assignment={assignment}
        checkboxes={false}
      />

      <Stack direction="row" sx={{ ml: 2 }} spacing={2}>
        <GraderLoadingButton
          color={submission?.edited ? 'error' : 'primary'}
          variant="outlined"
          onClick={setEditRepository}
        >
          {submission?.edited ? 'Reset ' : 'Create '} Edit Repository
        </GraderLoadingButton>

        <GraderLoadingButton
          color="primary"
          variant="outlined"
          disabled={!submission?.edited}
          onClick={handlePullEditedSubmission}
        >
          Pull Submission
        </GraderLoadingButton>

        <GraderLoadingButton
          variant="outlined"
          color="success"
          disabled={!submission?.edited}
          sx={{ ml: 2 }}
          onClick={() => {
            showDialog(
              'Edit Submission',
              'Do you want to push your submission changes?',
              pushEditedFiles
            );
          }}
        >
          Push Edited Submission
        </GraderLoadingButton>
      </Stack>

      <Box sx={{ flex: '1 1 100%' }} />

      <Toolbar>
        <Button variant="outlined" onClick={() => navigate(-1)}>
          Back
        </Button>
      </Toolbar>

      <SubmissionLogs
        open={showLogs}
        onClose={() => setShowLogs(false)}
        lectureId={lecture.id}
        assignmentId={assignment.id}
        submissionId={manualGradeSubmission.id}
      />
    </Stack>
  );
};
