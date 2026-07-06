/**
 * Copyright (c) 2022, TU Wien
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

import * as React from 'react';
import { Lecture } from '../../model/lecture';
import { Assignment } from '../../model/assignment';
import { Submission } from '../../model/submission';
import {
  Box,
  Button,
  Card,
  Chip,
  IconButton,
  LinearProgress,
  Stack,
  Tooltip,
  Typography
} from '@mui/material';
import ReplayIcon from '@mui/icons-material/Replay';
import { SubmissionList } from './submission-list';
import { AssignmentStatus } from './assignment-status';
import WarningIcon from '@mui/icons-material/Warning';
import { Outlet, useNavigate } from 'react-router-dom';
import {
  getAssignment,
  getAssignmentProperties,
  pullAssignment,
  pushAssignment,
  resetAssignment
} from '../../services/assignments.service';
import { getFiles, lectureBasePath } from '../../services/file.service';
import {
  getAllSubmissions,
  getSubmissionCount,
  submitAssignment
} from '../../services/submissions.service';
import { enqueueSnackbar } from 'notistack';
import { showDialog } from '../util/dialog-provider';
import RestartAltIcon from '@mui/icons-material/RestartAlt';
import GradingIcon from '@mui/icons-material/Grading';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import { DeadlineDetail } from '../util/deadline';
import moment from 'moment';
import { openBrowser } from '../coursemanage/overview/util';
import OpenInBrowserIcon from '@mui/icons-material/OpenInBrowser';
import { Scope, UserPermissions } from '../../services/permission.service';
import { GradeBook } from '../../services/gradebook';
import { useQuery } from '@tanstack/react-query';
import { getLecture } from '../../services/lectures.service';
import { extractIdsFromBreadcrumbs } from '../util/breadcrumbs';
import { FilesList } from '../util/file-list';
import { Contents } from '@jupyterlab/services';
import { GlobalObjects } from '../..';
import { RepoType } from '../util/repo-type';
import { FeedbackStatus } from '../../model/feedbackStatus';
import { AssignmentStatusEnum } from '../util/assignment-status-enum';

const calculateActiveStep = (
  submissions: Submission[],
  isAssignmentFetched: boolean
) => {
  const hasFeedback = submissions.reduce(
    (accum: boolean, curr: Submission) =>
      accum ||
      curr.feedback_status === FeedbackStatus.Generated ||
      curr.feedback_status === FeedbackStatus.FeedbackOutdated,
    false
  );
  if (hasFeedback) {
    return AssignmentStatusEnum.FEEDBACK_AVAILABLE;
  }
  if (submissions.length > 0) {
    return AssignmentStatusEnum.SUBMITTED;
  }
  if (isAssignmentFetched) {
    return AssignmentStatusEnum.PULLED;
  }
  return AssignmentStatusEnum.NOT_FETCHED;
};

interface ISubmissionsLeft {
  subLeft: number;
}

const SubmissionsLeftChip = (props: ISubmissionsLeft) => {
  const output =
    props.subLeft + ' submission' + (props.subLeft === 1 ? ' left' : 's left');
  return (
    <Chip sx={{ ml: 2 }} size="medium" icon={<WarningIcon />} label={output} />
  );
};

/**
 * Renders the components available in the extended assignment modal view
 */
export const AssignmentComponent = () => {
  const { lectureId, assignmentId } = extractIdsFromBreadcrumbs();

  const { data: lecture, isLoading: isLoadingLecture } = useQuery<Lecture>({
    queryKey: ['lecture', lectureId],
    queryFn: () => getLecture(lectureId),
    enabled: !!lectureId
  });

  const { data: assignment, isLoading: isLoadingAssignment } =
    useQuery<Assignment>({
      queryKey: ['assignment', assignmentId],
      queryFn: () => getAssignment(lectureId, assignmentId),
      enabled: !!lectureId && !!assignmentId
    });

  const { data: submissions = [], refetch: refetchSubmissions } = useQuery<
    Submission[]
  >({
    queryKey: ['submissionsAssignmentStudent', lectureId, assignmentId],
    queryFn: () => getAllSubmissions(lectureId, assignmentId, 'none', false),
    enabled: !!lectureId && !!assignmentId
  });

  const [fileList, setFileList] = React.useState<string[]>([]);
  const [activeStatus, setActiveStatus] = React.useState(
    AssignmentStatusEnum.NOT_FETCHED
  );
  const navigate = useNavigate();
  const reloadPage = () => navigate(0);

  const {
    data: subLeft,
    isLoading: isLoadingSubLeft,
    refetch: refetchSubleft
  } = useQuery<number>({
    queryKey: ['subLeft'],
    queryFn: async () => {
      await refetchSubmissions();
      const response = await getSubmissionCount(lectureId, assignmentId);
      const remainingSubmissions =
        assignment.settings.max_submissions - response.submission_count;
      return remainingSubmissions <= 0 ? 0 : remainingSubmissions;
    }
  });

  const {
    data: files,
    refetch: refetchFiles,
    isLoading: isLoadingFiles
  } = useQuery({
    queryKey: ['files', lectureId, assignmentId],
    queryFn: () =>
      getFiles(
        `${lectureBasePath}${lecture?.code}/assignments/${assignmentId}`
      ),
    enabled: !!lecture && !!assignment
  });

  const isAssignmentFetched = () => {
    return files.length > 0;
  };

  const path = `${lectureBasePath}${lecture?.code}/assignments/${assignment?.id}`;

  React.useEffect(() => {
    if (lecture && assignment && files) {
      getAssignmentProperties(lecture.id, assignment.id).then(properties => {
        const gb = new GradeBook(properties);
        setFileList([
          ...gb.getNotebooks().map(n => n + '.ipynb'),
          ...gb.getExtraFiles()
        ]);
        const active_step = calculateActiveStep(
          submissions,
          isAssignmentFetched()
        );
        setActiveStatus(active_step);
        refetchSubleft();
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
          reloadPage();
        }
      );
    }
  }, [lecture, assignment, submissions.length, files]);
  if (
    isLoadingAssignment ||
    isLoadingLecture ||
    isLoadingFiles ||
    isLoadingSubLeft
  ) {
    return (
      <div>
        <Card>
          <LinearProgress />
        </Card>
      </div>
    );
  }
  // Open the assignment in the JupyterLab file browser
  openBrowser(path);

  const resetAssignmentHandler = async () => {
    showDialog(
      'Reset Assignment',
      'This action will delete your current progress and reset the assignment!',
      async () => {
        try {
          await pushAssignment(
            lecture.id,
            assignment.id,
            RepoType.USER,
            'Pre-Reset'
          );
          await resetAssignment(lecture, assignment);
          await pullAssignment(lecture.id, assignment.id, RepoType.USER);
          enqueueSnackbar('Successfully Reset Assignment', {
            variant: 'success'
          });
          await refetchFiles();
        } catch (e) {
          if (e instanceof Error) {
            enqueueSnackbar('Error Reset Assignment: ' + e.message, {
              variant: 'error'
            });
          } else {
            console.error('Error: cannot interpret type unkown as error', e);
          }
        }
      }
    );
  };

  /**
   * Pushes the student submission and submits the assignment
   */
  const submitAssignmentHandler = async () => {
    showDialog(
      'Submit Assignment',
      'This action will submit your current notebooks!',
      async () => {
        await submitAssignment(lecture, assignment).then(
          () => {
            refetchSubleft().then(() => {
              const active_step = calculateActiveStep(
                submissions,
                isAssignmentFetched()
              );
              setActiveStatus(active_step);
            });
            enqueueSnackbar('Successfully Submitted Assignment', {
              variant: 'success'
            });
          },
          error => {
            enqueueSnackbar(error.message, {
              variant: 'error'
            });
          }
        );
      }
    );
  };

  /**
   * Pulls from given repository by sending a request to the grader git service.
   * @param repo input which repository should be fetched
   */
  const fetchAssignmentHandler = async (
    repo: RepoType.USER | RepoType.RELEASE
  ) => {
    await pullAssignment(lecture.id, assignment.id, repo).then(
      () => {
        enqueueSnackbar('Successfully Pulled Repo', {
          variant: 'success'
        });
        refetchFiles().then(() => {
          const active_step = calculateActiveStep(submissions, true);
          setActiveStatus(active_step);
        });
      },
      error => {
        enqueueSnackbar(error.message, {
          variant: 'error'
        });
      }
    );
  };

  const isDeadlineOver = () => {
    if (!assignment.settings.deadline) {
      return false;
    }
    const time = new Date(assignment.settings.deadline).getTime();
    return time < Date.now();
  };

  const isLateSubmissionOver = () => {
    const late_submission = assignment.settings.late_submission || [
      { period: 'P0D', scaling: undefined }
    ];
    // no late_submission entry found - check if deadline is over
    if (late_submission.length === 0) {
      return isDeadlineOver();
    }

    const late = moment(assignment.settings.deadline)
      .add(moment.duration(late_submission[late_submission.length - 1].period))
      .toDate()
      .getTime();
    return late < Date.now();
  };

  const isAssignmentCompleted = () => {
    return assignment.status === 'complete';
  };

  const isMaxSubmissionReached = () => {
    return (
      assignment.settings.max_submissions !== null &&
      assignment.settings.max_submissions <= submissions.length
    );
  };

  const hasPermissions = () => {
    const permissions = UserPermissions.getPermissions();
    const scope = permissions[lecture.code];
    return scope >= Scope.tutor;
  };

  return (
    <Box sx={{ flex: 1, overflow: 'auto' }}>
      <Box>
        <Box sx={{ mt: 6 }}>
          <Typography variant={'h6'} sx={{ ml: 2 }}>
            Status
          </Typography>
          <AssignmentStatus
            activeStep={activeStatus}
            submissions={submissions}
          />
        </Box>
        <Box sx={{ mt: 2, ml: 2 }}>
          <DeadlineDetail
            deadline={assignment.settings.deadline}
            late_submissions={assignment.settings.late_submission || []}
          />
        </Box>
        <Box sx={{ mt: 4 }}>
          <Stack
            direction={'row'}
            justifyContent={'flex-start'}
            alignItems={'center'}
            spacing={2}
            sx={{ ml: 2 }}
          >
            <Typography variant={'h6'} sx={{ ml: 2 }}>
              Files
            </Typography>
            <Tooltip title="Reload Files">
              <IconButton aria-label="reload" onClick={() => refetchFiles()}>
                <ReplayIcon />
              </IconButton>
            </Tooltip>
          </Stack>
          <FilesList
            files={files}
            sx={{ m: 2, mt: 1 }}
            lecture={lecture}
            shouldContain={fileList}
            assignment={assignment}
            checkboxes={false}
          />
          <Stack direction={'row'} spacing={1} sx={{ m: 1, ml: 2 }}>
            {!isAssignmentFetched() ? (
              <Tooltip title={'Fetch Assignment'}>
                <Button
                  variant="outlined"
                  color="primary"
                  size="small"
                  onClick={() => fetchAssignmentHandler(RepoType.USER)}
                >
                  <FileDownloadIcon fontSize="small" sx={{ mr: 1 }} />
                  Fetch
                </Button>
              </Tooltip>
            ) : null}

            <Tooltip title={'Submit Files in Assignment'}>
              <Button
                variant="outlined"
                color={!isDeadlineOver() ? 'success' : 'warning'}
                size="small"
                disabled={
                  hasPermissions()
                    ? false
                    : (isDeadlineOver() && isLateSubmissionOver()) ||
                      isMaxSubmissionReached() ||
                      isAssignmentCompleted() ||
                      files.length === 0
                }
                onClick={() => submitAssignmentHandler()}
              >
                <GradingIcon fontSize="small" sx={{ mr: 1 }} />
                Submit
              </Button>
            </Tooltip>

            <Tooltip title={'Reset Assignment to Released Version'}>
              <Button
                variant="outlined"
                size="small"
                color="error"
                onClick={() => resetAssignmentHandler()}
              >
                <RestartAltIcon fontSize="small" sx={{ mr: 1 }} />
                Reset
              </Button>
            </Tooltip>
            <Tooltip title={'Show files in JupyterLab file browser'}>
              <Button
                variant="outlined"
                size="small"
                color={'primary'}
                onClick={() => openBrowser(path)}
              >
                <OpenInBrowserIcon fontSize="small" sx={{ mr: 1 }} />
                Show in Filebrowser
              </Button>
            </Tooltip>
          </Stack>
        </Box>
        <Outlet />
      </Box>
      <Box sx={{ mt: 4 }}>
        <Typography variant={'h6'} sx={{ ml: 2, mt: 3 }}>
          Submissions
          {assignment.settings.max_submissions !== null ? (
            hasPermissions() ? (
              <Stack direction={'row'}>
                <SubmissionsLeftChip subLeft={subLeft} />
                <Chip
                  sx={{ ml: 2 }}
                  color="success"
                  variant="outlined"
                  label={'As instructor you have unlimited submissions'}
                />
              </Stack>
            ) : (
              <SubmissionsLeftChip subLeft={subLeft} />
            )
          ) : null}
        </Typography>
        <SubmissionList
          lecture={lecture}
          assignment={assignment}
          submissions={submissions}
          subLeft={subLeft}
          sx={{ m: 2, mt: 1 }}
        />
      </Box>
    </Box>
  );
};
