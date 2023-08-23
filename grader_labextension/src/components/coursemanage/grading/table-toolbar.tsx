import Toolbar from '@mui/material/Toolbar';
import { alpha } from '@mui/material/styles';
import Typography from '@mui/material/Typography';
import { Button, ButtonGroup, IconButton, Stack, ToggleButton, ToggleButtonGroup } from '@mui/material';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import ReplayIcon from '@mui/icons-material/Replay';
import CloudSyncIcon from '@mui/icons-material/CloudSync';
import * as React from 'react';
import { ltiSyncSubmissions } from '../../../services/submissions.service';
import { Assignment } from '../../../model/assignment';
import { Lecture } from '../../../model/lecture';
import { enqueueSnackbar } from 'notistack';
import { PageConfig } from '@jupyterlab/coreutils';
import { autogradeSubmission, generateFeedback, saveSubmissions } from '../../../services/grading.service';
import { lectureBasePath, openFile } from '../../../services/file.service';
import { Submission } from '../../../model/submission';
import { showDialog } from '../../util/dialog-provider';

export const autogradeSubmissionsDialog = async (handleAgree) => {
  showDialog(
    'Autograde Selected Submissions',
    'Do you wish to autograde the selected submissions?',
    handleAgree
  );
};

export const generateFeedbackDialog = async (handleAgree) => {
  showDialog(
    'Generate Feedback',
    'Do you wish to generate Feedback of the selected submissions?',
    handleAgree
  );
};

interface EnhancedTableToolbarProps {
  lecture: Lecture;
  assignment: Assignment;
  rows: Submission[];
  selected: readonly number[];
  shownSubmissions: 'none' | 'latest' | 'best';
  switchShownSubmissions: (event: React.MouseEvent<HTMLElement>, value: ('none' | 'latest' | 'best')) => void;
  clearSelection: () => void;
}

export function EnhancedTableToolbar(props: EnhancedTableToolbarProps) {
  const { lecture, assignment, rows, selected, shownSubmissions, switchShownSubmissions, clearSelection } = props;
  const numSelected = selected.length;
  const ltiEnabled = PageConfig.getOption('enable_lti_features') === 'true';

  const optionName = () => {
    if (props.shownSubmissions === 'latest') {
      return 'Latest';
    } else if (props.shownSubmissions === 'best') {
      return 'Best';
    } else {
      return 'All';
    }
  };

  const handleSyncSubmission = async () => {
    showDialog(
      'LTI Sync Submission',
      'Do you wish to sync Submissions?',
      async () => {
        await ltiSyncSubmissions(lecture.id, assignment.id)
          .then(response => {
            enqueueSnackbar(
              'Successfully matched ' +
              response.syncable_users +
              ' submissions with learning platform',
              { variant: 'success' }
            );
            enqueueSnackbar(
              'Successfully synced latest submissions with feedback of ' +
              response.synced_user +
              ' users',
              { variant: 'success' }
            );
          })
          .catch(error => {
            enqueueSnackbar(
              'Error while trying to sync submissions:' + error.message,
              { variant: 'error' }
            );
          });
      }
    );
  };

  const handleExportSubmissions = async () => {
    try {
      await saveSubmissions(lecture, assignment, shownSubmissions);
      await openFile(`${lectureBasePath}${lecture.code}/submissions.csv`);
      enqueueSnackbar('Successfully exported submissions', {
        variant: 'success'
      });
    } catch (err) {
      enqueueSnackbar('Error Exporting Submissions', {
        variant: 'error'
      });
    }
  };

  const handleAutogradeSubmissions = async () => {
    await autogradeSubmissionsDialog(async () => {
      try {
        await Promise.all(
          selected.map(async id => {
            const row = rows.find(value => value.id === id);
            row.auto_status = 'pending';
            await autogradeSubmission(
              lecture,
              assignment,
              row
            );
          }));
        enqueueSnackbar(`Autograding ${numSelected} submissions!`, {
          variant: 'success'
        });
      } catch (err) {
        console.error(err);
        enqueueSnackbar('Error Autograding Submissions', {
          variant: 'error'
        });
      }
      clearSelection();
    });
  };

  const handleGenerateFeedback = async () => {
    await generateFeedbackDialog(async () => {
      try {
        await Promise.all(
          selected.map(async id => {
            const row = rows.find(value => value.id === id);
            await generateFeedback(
              lecture.id,
              assignment.id,
              row.id
            );
          })
        );
        enqueueSnackbar(`Generating feedback for ${numSelected} submissions!`, {
          variant: 'success'
        });
      } catch (err) {
        console.error(err);
        enqueueSnackbar('Error Generating Feedback', {
          variant: 'error'
        });
      }
      clearSelection();
    });
  };

  return (
    <>
      <Toolbar
        sx={{
          pl: { sm: 2 },
          pr: { xs: 1, sm: 1 },
          ...(numSelected > 0 && {
            bgcolor: (theme) =>
              alpha(theme.palette.primary.main, theme.palette.action.activatedOpacity)
          })
        }}
      >
        {numSelected > 0 ? (
          <Typography
            sx={{ flex: '1 1 100%' }}
            color='inherit'
            variant='subtitle1'
            component='div'
          >
            {numSelected} selected
          </Typography>
        ) : (
          <Typography
            sx={{ flex: '1 1 100%' }}
            variant='h6'
            id='tableTitle'
            component='div'
          >
            Submissions
          </Typography>
        )}
        {numSelected > 0 ? (
          <ButtonGroup size='small' aria-label='autograde feedback buttons'>
            <Button key={'autograde'} sx={{ whiteSpace: 'nowrap', minWidth: 'auto' }}
                    onClick={handleAutogradeSubmissions}>
              Autograde
            </Button>
            <Button key={'feedback'} sx={{ whiteSpace: 'nowrap', minWidth: 'auto' }} onClick={handleGenerateFeedback}>
              {'Generate Feedback'}
            </Button>
          </ButtonGroup>
        ) : (
          <Stack direction='row' spacing={2}>
            <Button
              size='small'
              startIcon={<FileDownloadIcon />}
              sx={{ whiteSpace: 'nowrap', minWidth: 'auto' }}
              onClick={handleExportSubmissions}
            >
              {`Export ${optionName()} Submissions`}
            </Button>
            <Button
              size='small'
              startIcon={<CloudSyncIcon />}
              sx={{ whiteSpace: 'nowrap', minWidth: 'auto' }}
              disabled={!ltiEnabled}
              onClick={handleSyncSubmission}
            >
              LTI Sync Grades
            </Button>
            <ToggleButtonGroup
              size='small'
              color='primary'
              value={shownSubmissions}
              exclusive
              onChange={switchShownSubmissions}
              aria-label='shown submissions'
            >
              <ToggleButton value='none'>All</ToggleButton>
              <ToggleButton value='latest'>Latest</ToggleButton>
              <ToggleButton value='best'>Best</ToggleButton>
            </ToggleButtonGroup>
            <IconButton aria-label='reload' onClick={ev => switchShownSubmissions(ev, shownSubmissions)}>
              <ReplayIcon />
            </IconButton>
          </Stack>
        )}
      </Toolbar>
    </>
  );
}