import Toolbar from '@mui/material/Toolbar';
import { alpha } from '@mui/material/styles';
import Typography from '@mui/material/Typography';
import { Button, ButtonGroup, Stack, ToggleButton, ToggleButtonGroup } from '@mui/material';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import CloudSyncIcon from '@mui/icons-material/CloudSync';
import * as React from 'react';
import { AgreeDialog } from '../../util/dialog';
import { ltiSyncSubmissions } from '../../../services/submissions.service';
import { Assignment } from '../../../model/assignment';
import { Lecture } from '../../../model/lecture';
import { enqueueSnackbar } from 'notistack';
import { PageConfig } from '@jupyterlab/coreutils';

interface EnhancedTableToolbarProps {
  lecture: Lecture;
  assignment: Assignment;
  selected: readonly number[];
  shownSubmissions: 'none' | 'latest' | 'best';
  switchShownSubmissions: (event: React.MouseEvent<HTMLElement>, value: ('none' | 'latest' | 'best')) => void;
}

export function EnhancedTableToolbar(props: EnhancedTableToolbarProps) {
  const { lecture, assignment, selected, shownSubmissions, switchShownSubmissions } = props;
  const numSelected = selected.length;
  const ltiEnabled = PageConfig.getOption("enable_lti_features") === 'true';

  const [showDialog, setShowDialog] = React.useState(false);
  const [dialogContent, setDialogContent] = React.useState({
    title: '',
    message: '',
    handleAgree: null,
    handleDisagree: null
  });
  const closeDialog = () => setShowDialog(false);

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
    setDialogContent({
      title: 'LTI Sync Submission',
      message: 'Do you wish to sync Submissions?',
      handleAgree: async () => {
        await ltiSyncSubmissions(lecture.id, assignment.id)
          .then(response => {
            closeDialog();
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
            closeDialog();
            enqueueSnackbar(
              'Error while trying to sync submissions:' + error.message,
              { variant: 'error' }
            );
          });
      },
      handleDisagree: () => closeDialog()
    });
    setShowDialog(true);
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
            <Button key={'autograde'} sx={{ whiteSpace: 'nowrap', minWidth: 'auto' }}>
              Autograde
            </Button>
            <Button key={'feedback'} sx={{ whiteSpace: 'nowrap', minWidth: 'auto' }}>
              {'Generate Feedback'}
            </Button>
          </ButtonGroup>
        ) : (
          <Stack direction='row' spacing={2}>
            <Button
              size='small'
              startIcon={<FileDownloadIcon />}
              sx={{ whiteSpace: 'nowrap', minWidth: 'auto' }}
            >
              {`Export ${optionName()} Submissions`}
            </Button>
            <Button
              size='small'
              startIcon={<CloudSyncIcon />}
              sx={{ whiteSpace: 'nowrap', minWidth: 'auto' }}
              disabled={!ltiEnabled}
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
          </Stack>
        )}
      </Toolbar>
      <AgreeDialog open={showDialog} {...dialogContent} />
    </>
  );
}