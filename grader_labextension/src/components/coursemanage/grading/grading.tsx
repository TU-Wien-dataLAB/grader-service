// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import {
  DataGrid,
  GridRenderCellParams,
  GridSelectionModel
} from '@mui/x-data-grid';
import * as React from 'react';
import { Assignment } from '../../../model/assignment';
import { Lecture } from '../../../model/lecture';
import { utcToLocalFormat } from '../../../services/datetime.service';
import {
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  InputLabel,
  MenuItem,
  Typography,
  Tooltip,
  IconButton
} from '@mui/material';
import Select, { SelectChangeEvent } from '@mui/material/Select';
import {
  getAllSubmissions,
  ltiSyncSubmissions
} from '../../../services/submissions.service';
import { AgreeDialog } from '../../util/dialog';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import { ModalTitle } from '../../util/modal-title';
import { User } from '../../../model/user';
import { Submission } from '../../../model/submission';
import {
  autogradeSubmission,
  generateFeedback,
  saveSubmissions
} from '../../../services/grading.service';
import LoadingOverlay from '../../util/overlay';
import { ManualGrading } from './manual-grading';
import ReplayIcon from '@mui/icons-material/Replay';
import { GlobalObjects } from '../../../index';
import { enqueueSnackbar } from 'notistack';
import { loadString, storeString } from '../../../services/storage.service';
import CloudSyncIcon from '@mui/icons-material/CloudSync';
import { getConfig } from '../../../services/config.service';
/**
 * Props for GradingComponent.
 */
export interface IGradingProps {
  lecture: Lecture;
  assignment: Assignment;
  allSubmissions: Submission[];
  root: HTMLElement;
}

/**
 * .Rows object for the data grid.
 */
interface IRowValues extends Submission {
  sub_id: number;
}

/**
 * Renders the grading view in which the course management can grade student submissions and generate feedback.
 * @param props Props of the grading component
 */
export const GradingComponent = (props: IGradingProps) => {
  const [option, setOption] = React.useState(
    (loadString('grading-submission-option', null, props.assignment) ||
      'none') as 'none' | 'latest' | 'best'
  );
  const [showDialog, setShowDialog] = React.useState(false);
  const [showLogs, setShowLogs] = React.useState(false);
  const [showSyncGrades, setSyncGrades] = React.useState(false);
  const [logs, setLogs] = React.useState(undefined);
  const [dialogContent, setDialogContent] = React.useState({
    title: '',
    message: '',
    handleAgree: null,
    handleDisagree: null
  });

  const [displayManualGrading, setDisplayManualGrading] = React.useState(false);
  const onManualGradingClose = async () => {
    setDisplayManualGrading(false);
  };
  /**
   * Removes row selection.
   */
  const cleanSelectedRows = () => {
    setSelectedRows([]);
  };
  /**
   * Automatically grade selected submissions.
   */
  const handleAutogradeSubmissions = async () => {
    setDialogContent({
      title: 'Autograde Selected Submissions',
      message: 'Do you wish to autograde the selected submissions?',
      handleAgree: async () => {
        try {
          const numSubs = selectedRowsData.length;
          selectedRowsData.map(async row => {
            row.auto_status = 'pending';
            await autogradeSubmission(
              props.lecture,
              props.assignment,
              getSubmissionFromRow(row)
            );
          });
        } catch (err) {
          console.error(err);
          enqueueSnackbar('Error Autograding Submissions', {
            variant: 'error'
          });
        }
        cleanSelectedRows();
        closeDialog();
      },
      handleDisagree: () => closeDialog()
    });
    setShowDialog(true);
  };
  /**
   * Generate feedback for selected submissions.
   */
  const handleGenerateFeedback = async () => {
    setDialogContent({
      title: 'Generate Feedback',
      message: 'Do you wish to generate Feedback of the selected submissions?',
      handleAgree: async () => {
        try {
          const numSubs = selectedRowsData.length;
          await Promise.all(
            selectedRowsData.map(async row => {
              await generateFeedback(
                props.lecture.id,
                props.assignment.id,
                row.id
              );
            })
          );
          getAllSubmissions(
            props.lecture,
            props.assignment,
            option,
            true,
            true
          ).then(response => {
            setRows(generateRows(response));
            enqueueSnackbar(`Generating Feedback for ${numSubs} Submissions`, {
              variant: 'success'
            });
          });
        } catch (err) {
          console.error(err);
          enqueueSnackbar('Error Generating Feedback', {
            variant: 'error'
          });
        }
        cleanSelectedRows();
        closeDialog();
      },
      handleDisagree: () => closeDialog()
    });
    setShowDialog(true);
  };

  const getConfigFromService = () => {
    getConfig().then(response => {
      setSyncGrades(response['enable_lti_features']);
    });
  };

  /**
   * Closes dialog window.
   */
  const closeDialog = () => setShowDialog(false);
  /**
   * Generates rows objects out of submission.
   * @param submissions submissions which are used to generate row objects
   */
  const generateRows = (submissions: Submission[]) => {
    const rows: IRowValues[] = [];
    let id = 1;
    submissions.forEach((sub: Submission) => {
      rows.push({
        id: sub.id,
        sub_id: id++,
        username: sub.username,
        submitted_at: utcToLocalFormat(sub.submitted_at),
        auto_status: sub.auto_status,
        manual_status: sub.manual_status,
        logs: sub.logs,
        commit_hash: sub.commit_hash,
        feedback_available: sub.feedback_available,
        score: sub.score
      });
    });
    return rows;
  };

  const [submissions, setSubmissions] = React.useState(props.allSubmissions);
  const [rows, setRows] = React.useState([]);

  const [selectedRows, setSelectedRows] = React.useState<GridSelectionModel>(
    []
  );
  const [selectedRowsData, setSelectedRowsData] = React.useState(
    [] as IRowValues[]
  );
  /**
   * Updates rows by setting the new value of the submission select.
   * @param event select change event
   */
  const handleChange = (event: SelectChangeEvent) => {
    setOption(event.target.value as 'none' | 'latest' | 'best');
    storeString(
      'grading-submission-option',
      event.target.value,
      null,
      props.assignment
    );
  };
  /**
   * Updates submissions and rows.
   */
  const updateSubmissions = () => {
    getAllSubmissions(props.lecture, props.assignment, option, true, true).then(
      response => {
        setRows(generateRows(response));
        setSubmissions(response);
      }
    );
  };

  React.useEffect(() => {
    updateSubmissions();
    getConfigFromService();
  }, [option, displayManualGrading]);
  /**
   * Calculates chip color based on submission status.
   * @param value submission status
   * @return chip color
   */
  const getColor = (value: string) => {
    if (value === 'not_graded') {
      return 'warning';
    } else if (
      value === 'automatically_graded' ||
      value === 'manually_graded'
    ) {
      return 'success';
    } else if (value === 'grading_failed') {
      return 'error';
    }
    return 'primary';
  };
  /**
   * Opens log dialog which contain autograded logs from grader service.
   * @param params row which is needed to find selected submission
   */
  const openLogs = (params: GridRenderCellParams<string>) => {
    const submission: Submission = getSubmissionFromRow(
      params.row as IRowValues
    );
    const logs = submission.logs;
    if (logs === undefined || logs === null || logs === '') {
      enqueueSnackbar('No logs for submission', {
        variant: 'error'
      });
      return;
    }
    setLogs(logs);
    setShowLogs(true);
  };

  const columns = [
    { field: 'sub_id', headerName: 'No.', width: 110 },
    { field: 'username', headerName: 'User', width: 130 },
    { field: 'submitted_at', headerName: 'Date', width: 170 },
    {
      field: 'auto_status',
      headerName: 'Autograde-Status',
      width: 200,
      renderCell: (params: GridRenderCellParams<string>) => (
        <Chip
          variant="outlined"
          label={params.value}
          color={getColor(params.value)}
          clickable={true}
          onClick={() => openLogs(params)}
        />
      )
    },
    {
      field: 'manual_status',
      headerName: 'Manualgrade-Status',
      width: 170,
      renderCell: (params: GridRenderCellParams<string>) => (
        <Chip
          variant="outlined"
          label={params.value}
          color={getColor(params.value)}
        />
      )
    },
    {
      field: 'feedback_available',
      headerName: 'Feedback generated',
      width: 170,
      renderCell: (params: GridRenderCellParams<boolean>) => (
        <Chip
          variant="outlined"
          label={params.value ? 'Generated' : 'Not Generated'}
          color={params.value ? 'success' : 'error'}
        />
      )
    },
    { field: 'score', headerName: 'Score', width: 130 }
  ];
  /**
   * Returns submission based on given rows.
   * @param row row which is needed to determine submission
   */
  const getSubmissionFromRow = (row: IRowValues): Submission => {
    // Leave linear search for now (there were problems with casting and the local display date when casting)
    if (row === undefined) {
      return null;
    }
    const id = row.id;
    const submission = submissions.find(s => s.id === id);
    return submission === undefined ? null : submission;
  };

  const allAutoGraded = (selection: IRowValues[]) => {
    return selection.reduce((acc, cur) => {
      return cur.auto_status === 'automatically_graded' && acc;
    }, true);
  };

  const allManualGraded = (selection: IRowValues[]) => {
    return selection.reduce((acc, cur) => {
      return cur.manual_status === 'manually_graded' && acc;
    }, true);
  };

  const optionName = () => {
    if (option === 'latest') {
      return 'Latest';
    } else if (option === 'best') {
      return 'Best';
    } else {
      return 'All';
    }
  };

  const openFile = async (path: string) => {
    GlobalObjects.commands
      .execute('docmanager:open', {
        path: path,
        options: {
          mode: 'tab-after' // tab-after tab-before split-bottom split-right split-left split-top
        }
      })
      .catch(error => {
        enqueueSnackbar(error.message, {
          variant: 'error'
        });
      });
  };
  /**
   * Exports submissions.
   */
  const handleExportSubmissions = async () => {
    try {
      await saveSubmissions(props.lecture, props.assignment, option);
      await openFile(`${props.lecture.code}/submissions.csv`);
      enqueueSnackbar('Successfully exported submissions', {
        variant: 'success'
      });
    } catch (err) {
      enqueueSnackbar('Error Exporting Submissions', {
        variant: 'error'
      });
    }
  };

  const handleSyncSubmission = async () => {
    setDialogContent({
      title: 'LTI Sync Submission',
      message: 'Do you wish to sync Submissions?',
      handleAgree: async () => {
        await ltiSyncSubmissions(props.lecture.id, props.assignment.id)
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
    <div>
      <ModalTitle title="Grading">
        <Box sx={{ ml: 2 }} display="inline-block">
          <Tooltip title="Reload">
            <IconButton aria-label="reload" onClick={updateSubmissions}>
              <ReplayIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </ModalTitle>
      <div style={{ display: 'flex', height: '50vh', marginTop: '30px' }}>
        <div style={{ flexGrow: 1 }}>
          <DataGrid
            sx={{ mb: 3, ml: 3, mr: 3 }}
            columns={columns}
            rows={rows}
            checkboxSelection
            disableSelectionOnClick
            selectionModel={selectedRows}
            onSelectionModelChange={e => {
              const selectedIDs = new Set(e);
              const selectedRowData = rows.filter(row =>
                selectedIDs.has(row.id)
              );
              setSelectedRows(e);
              setSelectedRowsData(selectedRowData);
            }}
          />
        </div>
      </div>
      <span style={{ height: '15vh' }}>
        <FormControl sx={{ m: 3 }}>
          <InputLabel id="submission-select-label">View</InputLabel>
          <Select
            labelId="submission-select-label"
            id="submission-select"
            value={option}
            label="Age"
            onChange={handleChange}
          >
            <MenuItem value={'none'}>All Submissions</MenuItem>
            <MenuItem value={'latest'}>Latest Submissions of Users</MenuItem>
            <MenuItem value={'best'}>Best Submissions of Users</MenuItem>
          </Select>
        </FormControl>
        <Tooltip
          title={`Run Autograde Tests for ${selectedRows.length} Submission${
            selectedRows.length === 1 ? '' : 's'
          }`}
        >
          <Button
            disabled={selectedRows.length === 0}
            sx={{ m: 3 }}
            variant="outlined"
            onClick={handleAutogradeSubmissions}
          >
            {`Autograde (${selectedRows.length})`}
          </Button>
        </Tooltip>
        <NavigateNextIcon
          color={
            selectedRowsData.length === 1 &&
            selectedRowsData[0]?.auto_status !== 'automatically_graded'
              ? 'error'
              : selectedRowsData.length !== 1 ||
                selectedRowsData[0]?.auto_status !== 'automatically_graded'
              ? 'disabled'
              : 'primary'
          }
          sx={{ mb: -1 }}
        />
        <Tooltip title={'Manually Grade Answers of Submission'}>
          <Button
            disabled={
              selectedRowsData.length !== 1 ||
              selectedRowsData[0]?.auto_status !== 'automatically_graded'
            }
            sx={{ m: 3 }}
            onClick={() => {
              cleanSelectedRows();
              setDisplayManualGrading(true);
            }}
            variant="outlined"
          >
            {'Manualgrade'}
          </Button>
        </Tooltip>
        <NavigateNextIcon
          color={
            selectedRows.length === 0
              ? 'disabled'
              : allManualGraded(selectedRowsData) ||
                props.assignment.automatic_grading === 'full_auto'
              ? 'primary'
              : 'error'
          }
          sx={{ mb: -1 }}
        />
        <Tooltip title={'Generate and Publish Feedback'}>
          <Button
            disabled={
              selectedRows.length === 0 ||
              (props.assignment.automatic_grading !== 'full_auto' &&
                !allAutoGraded(selectedRowsData))
            }
            sx={{ m: 3 }}
            onClick={handleGenerateFeedback}
            variant="outlined"
          >
            {`Generate Feedback (${selectedRows.length})`}
          </Button>
        </Tooltip>

        <Button
          startIcon={<FileDownloadIcon />}
          sx={{ m: 3 }}
          onClick={handleExportSubmissions}
          variant="outlined"
        >
          {`Export ${optionName()} Submissions`}
        </Button>

        <Button
          variant="outlined"
          startIcon={<CloudSyncIcon />}
          sx={{ m: 3 }}
          disabled={!showSyncGrades}
          onClick={handleSyncSubmission}
        >
          {showSyncGrades
            ? 'LTI Sync Grades'
            : 'LTI Sync Grades (disabled by grader service)'}
        </Button>
      </span>

      <LoadingOverlay
        onClose={onManualGradingClose}
        open={displayManualGrading}
        container={props.root}
        transition="zoom"
      >
        <ManualGrading
          lecture={props.lecture}
          assignment={props.assignment}
          submission={getSubmissionFromRow(selectedRowsData[0])}
          username={selectedRowsData[0]?.username}
          onClose={onManualGradingClose}
        />
      </LoadingOverlay>

      {/* Dialog */}
      <AgreeDialog open={showDialog} {...dialogContent} />
      <Dialog
        open={showLogs}
        onClose={() => setShowLogs(false)}
        aria-labelledby="alert-dialog-title"
        aria-describedby="alert-dialog-description"
      >
        <DialogTitle id="alert-dialog-title">{'Logs'}</DialogTitle>
        <DialogContent>
          <Typography
            id="alert-dialog-description"
            sx={{ fontSize: 10, fontFamily: "'Roboto Mono', monospace" }}
          >
            {logs}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowLogs(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </div>
  );
};
