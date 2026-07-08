import {
  Alert,
  AlertTitle,
  Box,
  Button,
  Card,
  LinearProgress,
  Stack,
  TextField,
  Typography
} from '@mui/material';
import * as React from 'react';
import { Lecture } from '../../../model/lecture';
import { Assignment } from '../../../model/assignment';
import { FilesList } from '../../util/file-list';
import {
  lectureBasePath,
  getFiles,
  makeDirs
} from '../../../services/file.service';
import { Link, useOutletContext } from 'react-router-dom';
import { showDialog } from '../../util/dialog-provider';
import Autocomplete from '@mui/material/Autocomplete';
import { Contents } from '@jupyterlab/services';
import { GlobalObjects } from '../../../index';
import { openBrowser } from '../overview/util';
import { createSubmissionFiles } from '../../../services/submissions.service';
import { enqueueSnackbar } from 'notistack';
import { GraderLoadingButton } from '../../util/loading-button';
import { useQuery, useMutation } from '@tanstack/react-query';
import { getLecture, getUsers } from '../../../services/lectures.service';
import { extractIdsFromBreadcrumbs } from '../../util/breadcrumbs';

export const CreateSubmission = () => {
  const { assignment } = useOutletContext() as {
    assignment: Assignment;
  };

  const { lectureId } = extractIdsFromBreadcrumbs();

  const { data: lecture, isLoading: isLoadingLecture } = useQuery<Lecture>({
    queryKey: ['lecture', lectureId],
    queryFn: () => getLecture(lectureId, true),
    enabled: !!lectureId
  });

  const { data: students, isLoading: isLoadingStudents } = useQuery({
    queryKey: ['students', lectureId],
    queryFn: async () => {
      const users = await getUsers(lectureId);
      return users['students'].map(s => s.name);
    },
    enabled: !!lectureId
  });

  const [userDir, setUserDir] = React.useState<string | null>(null);

  const path =
    lecture && assignment && userDir
      ? `${lectureBasePath}${lecture.code}/create/${assignment.id}/${userDir}`
      : null;
  openBrowser(path);

  const { data: files = [], refetch: refetchFiles } = useQuery({
    queryKey: ['submissionFiles', path],
    queryFn: () => (path ? getFiles(path) : Promise.resolve([])),
    enabled: !!path
  });

  const createSubmissionMutation = useMutation({
    mutationFn: async () => {
      if (lecture && assignment && userDir) {
        return createSubmissionFiles(lecture, assignment, userDir);
      }
    },
    onError: (error: any) => {
      enqueueSnackbar('Error: ' + error.message, { variant: 'error' });
    },
    onSuccess: () => {
      enqueueSnackbar(`Successfully Created Submission for user: ${userDir}`, {
        variant: 'success'
      });
      refetchFiles();
    }
  });

  React.useEffect(() => {
    if (path) {
      makeDirs(`${lectureBasePath}${lecture.code}`, [
        'create',
        `${assignment.id}`,
        userDir
      ]).then(() => {
        openBrowser(path);
      });

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
    }
  }, [userDir]);

  if (isLoadingLecture || isLoadingStudents) {
    return (
      <Card>
        <LinearProgress />
      </Card>
    );
  }

  const createSubmission = () => {
    showDialog(
      'Manual Submission',
      'Do you want to push new submission?',
      async () => {
        createSubmissionMutation.mutate();
      }
    );
  };

  const submissionsLink = `/lecture/${lecture.id}/assignment/${assignment.id}/submissions`;

  return (
    <Box sx={{ overflow: 'auto' }}>
      <Stack direction="column" sx={{ flex: '1 1 100%' }}>
        <Alert severity="info" sx={{ m: 2 }}>
          <AlertTitle>Info</AlertTitle>
          Follow these steps to manually create a submission:
          <br />
          <br />
          1. Select the student.
          <br />
          2. The submission folder will open in the File Browser.
          <br />
          3. Upload files. They appear below.
          <br />
          4. Push the submission.
        </Alert>

        <Typography sx={{ m: 2, mb: 0 }}>Select a student</Typography>
        <Autocomplete
          options={students}
          autoHighlight
          value={userDir}
          onChange={(event, newUserDir) => setUserDir(newUserDir)}
          sx={{ m: 2 }}
          renderInput={params => (
            <TextField {...params} label="Select Student" />
          )}
        />

        <Typography sx={{ ml: 2 }}>Submission Files</Typography>
        <FilesList
          files={files}
          sx={{ m: 2 }}
          lecture={lecture}
          assignment={assignment}
          checkboxes={false}
        />

        <Stack direction="row" sx={{ ml: 2 }} spacing={2}>
          <GraderLoadingButton
            variant="outlined"
            color="success"
            sx={{ ml: 2 }}
            onClick={createSubmission}
          >
            Push Submission
          </GraderLoadingButton>
        </Stack>

        <Stack sx={{ ml: 2, mt: 3, mb: 5 }} direction="row">
          <Button
            variant="outlined"
            component={Link as any}
            to={submissionsLink}
          >
            Back
          </Button>
        </Stack>
      </Stack>
    </Box>
  );
};
