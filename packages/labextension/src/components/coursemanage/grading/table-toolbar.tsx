import Toolbar from '@mui/material/Toolbar';
import { alpha } from '@mui/material/styles';
import Typography from '@mui/material/Typography';
import {
  Button,
  ButtonGroup,
  FormControl,
  IconButton,
  Input,
  InputAdornment,
  Stack,
  ToggleButton,
  ToggleButtonGroup,
  Tooltip
} from '@mui/material';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import ReplayIcon from '@mui/icons-material/Replay';
import * as React from 'react';
import { Assignment } from '../../../model/assignment';
import { Lecture } from '../../../model/lecture';
import { enqueueSnackbar } from 'notistack';
import {
  autogradeSubmission,
  generateFeedback,
  saveSubmissions
} from '../../../services/grading.service';
import { lectureBasePath, openFile } from '../../../services/file.service';
import { Submission } from '../../../model/submission';
import { showDialog } from '../../util/dialog-provider';
import SearchIcon from '@mui/icons-material/Search';
import ClearIcon from '@mui/icons-material/Clear';
import { queryClient } from '../../../widgets/assignmentmanage';
import { SyncSubmissionGradesDialog } from '../../util/dialog';
import { openBrowser } from '../overview/util';
import { loadString, storeString } from '../../../services/storage.service';
import { ltiSyncSubmissions } from '../../../services/submissions.service';
import { AutoStatus } from '../../../model/autoStatus';
import { FeedbackStatus } from '../../../model/feedbackStatus';

export const autogradeSubmissionsDialog = async handleAgree => {
  showDialog(
    'Autograde Selected Submissions',
    'Do you wish to autograde the selected submissions?',
    handleAgree
  );
};

export const generateFeedbackDialog = async handleAgree => {
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
  switchShownSubmissions: (
    event: React.MouseEvent<HTMLElement>,
    value: 'none' | 'latest' | 'best'
  ) => void;
  clearSelection: () => void;
  setSearch: React.Dispatch<React.SetStateAction<string>>;
}

export function EnhancedTableToolbar(props: EnhancedTableToolbarProps) {
  const {
    lecture,
    assignment,
    rows,
    selected,
    shownSubmissions,
    switchShownSubmissions,
    clearSelection,
    setSearch
  } = props;
  const numSelected = selected.length;

  const [searchTerm, setSearchTerm] = React.useState(
    () => loadString(`grader-search-${assignment.id}`) || ''
  );
  const searchTimeout = React.useRef(null);

  const handleSearch = event => {
    const value = event.target.value;
    setSearchTerm(value);

    if (searchTimeout.current) {
      clearTimeout(searchTimeout.current);
    }
    searchTimeout.current = setTimeout(() => {
      storeString(`grader-search-${assignment.id}`, value.toLowerCase());
      setSearch(value.toLowerCase());
    }, 250);
  };

  const handleClear = () => {
    setSearchTerm('');
    storeString(`grader-search-${assignment.id}`, '');
    setSearch('');
  };

  const optionName = () => {
    if (props.shownSubmissions === 'latest') {
      return 'Latest';
    } else if (props.shownSubmissions === 'best') {
      return 'Best';
    } else {
      return 'All';
    }
  };

  const handleExportSubmissions = async () => {
    try {
      await saveSubmissions(lecture, assignment, shownSubmissions);
      await openFile(
        `${lectureBasePath}${lecture.code}/assignments/${assignment.id}/${assignment.name}_${shownSubmissions}_submissions.csv`
      );
      await openBrowser(
        `${lectureBasePath}${lecture.code}/assignments/${assignment.id}`
      );
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
            row.auto_status = AutoStatus.Pending;
            await autogradeSubmission(lecture, assignment, row);
            await queryClient.invalidateQueries({
              queryKey: ['submissionLogs', lecture.id, assignment.id, row.id]
            });
          })
        );
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
            row.feedback_status = FeedbackStatus.Generating;
            await generateFeedback(lecture, assignment, row);
          })
        );
        enqueueSnackbar(`Generating feedback for ${numSelected} submissions!`, {
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
      clearSelection();
    });
  };

  const notifyLtiSyncResult = (
    syncedPlatforms: Array<{
      platform: string;
      syncable_users: number;
      synced_user: number;
    }>
  ) => {
    if (!syncedPlatforms.length) {
      enqueueSnackbar(
        'No connected learning platform was available for grade sync',
        {
          variant: 'info'
        }
      );
      return;
    }

    syncedPlatforms.forEach(platformResult => {
      enqueueSnackbar(
        `${platformResult.platform}: Synced ${platformResult.synced_user}/${platformResult.syncable_users} users`,
        { variant: 'success' }
      );
    });
  };

  const handleLTISyncGrades = () => {
    ltiSyncSubmissions(lecture.id, assignment.id, 'selection', [
      ...selected
    ]).then(
      response => {
        notifyLtiSyncResult(response.synced_platforms);
      },
      () => {
        enqueueSnackbar('Error Syncing Grades', { variant: 'error' });
      }
    );
  };

  const checkAutogradeStatus = () => {
    let available = true;
    selected.forEach(async id => {
      const row = rows.find(value => value.id === id);
      if (row.auto_status !== AutoStatus.AutomaticallyGraded) {
        available = false;
      }
    });
    return available;
  };

  return (
    <>
      <Toolbar
        sx={{
          pl: { sm: 2 },
          pr: { xs: 1, sm: 1 },
          ...(numSelected > 0 && {
            bgcolor: theme =>
              alpha(
                theme.palette.primary.main,
                theme.palette.action.activatedOpacity
              )
          })
        }}
      >
        {numSelected > 0 ? (
          <Typography
            sx={{ flex: '1 1 100%' }}
            color="inherit"
            variant="subtitle1"
            component="div"
          >
            {numSelected} selected
          </Typography>
        ) : (
          <Stack direction="row" spacing={2} sx={{ flex: '1 1 100%' }}>
            <Typography variant="h6" id="tableTitle" component="div">
              Submissions
            </Typography>
            <FormControl sx={{ m: 1, width: '25ch' }} variant="standard">
              <Input
                id="search"
                type="search"
                value={searchTerm}
                onChange={handleSearch}
                size={'small'}
                sx={{ width: 200 }}
                startAdornment={
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                }
                endAdornment={
                  searchTerm !== '' ? (
                    <InputAdornment position="end">
                      <IconButton
                        size={'small'}
                        aria-label="clear search"
                        onClick={handleClear}
                        edge="end"
                      >
                        <ClearIcon />
                      </IconButton>
                    </InputAdornment>
                  ) : null
                }
              />
            </FormControl>
          </Stack>
        )}
        {numSelected > 0 ? (
          <ButtonGroup size="small" aria-label="autograde feedback buttons">
            <Tooltip
              title={
                'To generate feedback all selected submissions must be autograded.'
              }
            >
              <Button
                key={'autograde'}
                sx={{ whiteSpace: 'nowrap', minWidth: 'auto' }}
                onClick={handleAutogradeSubmissions}
              >
                Autograde
              </Button>
            </Tooltip>
            <Tooltip
              title={
                checkAutogradeStatus()
                  ? 'Generate feedback for all selected submissions'
                  : 'All selected submissions have to be automatically graded!'
              }
            >
              <span>
                <Button
                  key={'feedback'}
                  sx={{ whiteSpace: 'nowrap', minWidth: 'auto' }}
                  disabled={!checkAutogradeStatus()}
                  onClick={handleGenerateFeedback}
                >
                  Generate Feedback
                </Button>
              </span>
            </Tooltip>
            <Button
              key={'lti'}
              sx={{ whiteSpace: 'nowrap', minWidth: 'auto' }}
              disabled={!checkAutogradeStatus()}
              onClick={handleLTISyncGrades}
            >
              LTI Sync Grades
            </Button>
          </ButtonGroup>
        ) : (
          <Stack direction="row" spacing={2}>
            <Button
              size="small"
              startIcon={<FileDownloadIcon />}
              sx={{ whiteSpace: 'nowrap', minWidth: 'auto' }}
              onClick={handleExportSubmissions}
            >
              {`Export ${optionName()} Submissions`}
            </Button>
            <SyncSubmissionGradesDialog
              lecture={lecture}
              assignment={assignment}
            />
            <ToggleButtonGroup
              size="small"
              color="primary"
              value={shownSubmissions}
              exclusive
              onChange={switchShownSubmissions}
              aria-label="shown submissions"
            >
              <ToggleButton value="none">All</ToggleButton>
              <ToggleButton value="latest">Latest</ToggleButton>
              <ToggleButton value="best">Best</ToggleButton>
            </ToggleButtonGroup>
            <IconButton
              aria-label="reload"
              onClick={ev => switchShownSubmissions(ev, shownSubmissions)}
            >
              <ReplayIcon />
            </IconButton>
          </Stack>
        )}
      </Toolbar>
    </>
  );
}
