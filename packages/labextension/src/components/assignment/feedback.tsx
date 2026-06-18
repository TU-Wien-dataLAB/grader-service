// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.
import { SectionTitle } from '../util/section-title';
import { Box, Button, Stack, Tooltip, Typography } from '@mui/material';
import * as React from 'react';
import { Lecture } from '../../model/lecture';
import { Assignment } from '../../model/assignment';
import { Submission } from '../../model/submission';
import {
  getProperties,
  getSubmission,
  pullFeedback
} from '../../services/submissions.service';
import { GradeBook } from '../../services/gradebook';
import { FilesList } from '../util/file-list';
import { openBrowser } from '../coursemanage/overview/util';
import OpenInBrowserIcon from '@mui/icons-material/OpenInBrowser';
import { getFiles, lectureBasePath } from '../../services/file.service';
import { Link, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getLecture } from '../../services/lectures.service';
import { getAssignment } from '../../services/assignments.service';
import { extractIdsFromBreadcrumbs } from '../util/breadcrumbs';
import { enqueueSnackbar } from 'notistack';

export const Feedback = () => {
  const { lectureId, assignmentId } = extractIdsFromBreadcrumbs();
  const params = useParams();
  const submissionId = +params['sid'];

  const { data: lecture, isLoading: isLoadingLecture } = useQuery<Lecture>({
    queryKey: ['lecture', lectureId],
    queryFn: () => getLecture(lectureId),
    enabled: !!lectureId
  });

  const { data: assignment, isLoading: isLoadingAssignment } =
    useQuery<Assignment>({
      queryKey: ['assignment', assignmentId],
      queryFn: () => getAssignment(lectureId, assignmentId),
      enabled: !!lecture && !!assignmentId
    });

  const { data: submission, isLoading: isLoadingSubmission } =
    useQuery<Submission>({
      queryKey: ['submission', lectureId, assignmentId, submissionId],
      queryFn: () => getSubmission(lectureId, assignmentId, submissionId),
      enabled: !!lecture && !!assignment
    });

  const feedbackPath = `${lectureBasePath}${lecture.code}/feedback/${assignmentId}/${submissionId}`;
  openBrowser(feedbackPath);

  const { data: gradeBook } = useQuery({
    queryKey: ['gradeBook', submissionId],
    queryFn: () =>
      submission
        ? getProperties(lectureId, assignmentId, submissionId).then(
            properties => new GradeBook(properties)
          )
        : Promise.resolve(null),
    enabled: !!submission
  });

  const { data: files = [], refetch: refetchFiles } = useQuery({
    queryKey: ['submissionFiles', lectureId, assignmentId, submissionId],
    queryFn: () => {
      return getFiles(feedbackPath);
    },
    enabled: !!lecture?.code && !!assignmentId && !!submissionId
  });

  const assignmentLink = `/lecture/${lecture?.id}/assignment/${assignment?.id}`;

  if (isLoadingAssignment || isLoadingLecture || isLoadingSubmission) {
    return <div>Loading...</div>;
  }

  const handlePullFeedback = async () => {
    await pullFeedback(lecture, assignment, submission)
      .then(() => {
        enqueueSnackbar('Feedback pulled successfully', {
          variant: 'success'
        });
        refetchFiles();
      })
      .catch(error => {
        enqueueSnackbar(`Error pulling feedback: ${error}`, {
          variant: 'error'
        });
      });
  };

  return (
    <Box sx={{ overflow: 'auto' }}>
      <SectionTitle title={`Feedback for ${assignment.name}`} />
      <Box sx={{ m: 2, mt: 12 }}>
        <Stack direction="row" spacing={2} sx={{ ml: 2 }}>
          <Stack sx={{ mt: 0.5 }}>
            {['Lecture', 'Assignment', 'Points', 'Extra Credit'].map(label => (
              <Typography
                key={label}
                textAlign="right"
                color="text.secondary"
                sx={{ fontSize: 12, height: 35 }}
              >
                {label}
              </Typography>
            ))}
          </Stack>
          <Stack>
            <Typography
              color="text.primary"
              sx={{ display: 'inline-block', fontSize: 16, height: 35 }}
            >
              {lecture.name}
            </Typography>
            <Typography
              color="text.primary"
              sx={{ display: 'inline-block', fontSize: 16, height: 35 }}
            >
              {assignment.name}
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
          </Stack>
        </Stack>
      </Box>

      <Typography sx={{ m: 2, mb: 0 }}>Feedback Files</Typography>
      <FilesList
        files={files}
        sx={{ m: 2, overflow: 'auto' }}
        lecture={lecture}
        assignment={assignment}
        checkboxes={false}
      />

      <Stack direction="row" spacing={2} sx={{ m: 2 }}>
        <Button variant="outlined" component={Link as any} to={assignmentLink}>
          Back
        </Button>
        <Button
          variant="outlined"
          size="small"
          color="primary"
          onClick={handlePullFeedback}
        >
          Pull Feedback
        </Button>
        <Tooltip title="Show files in JupyterLab file browser">
          <Button
            variant="outlined"
            size="small"
            color="primary"
            onClick={() => openBrowser(feedbackPath)}
          >
            <OpenInBrowserIcon fontSize="small" sx={{ mr: 1 }} />
            Show in Filebrowser
          </Button>
        </Tooltip>
      </Stack>
    </Box>
  );
};
