// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import * as React from 'react';

import { Assignment } from '../../../model/assignment';
import { Lecture } from '../../../model/lecture';
import { SectionTitle } from '../../util/section-title';
import { OverviewCard } from './overview-card';
import { Box, Card, LinearProgress } from '@mui/material';
import { AssignmentStatus } from './assignment-status';
import { useQuery } from '@tanstack/react-query';
import { getAssignment } from '../../../services/assignments.service';
import { extractIdsFromBreadcrumbs } from '../../util/breadcrumbs';
import { getLecture, getUsers } from '../../../services/lectures.service';
import { getAllSubmissions } from '../../../services/submissions.service';

export const OverviewComponent = () => {
  const { lectureId, assignmentId } = extractIdsFromBreadcrumbs();

  const { data: lecture, isLoading: isLoadingLecture } = useQuery<Lecture>({
    queryKey: ['lecture', lectureId],
    queryFn: () => getLecture(lectureId),
    enabled: !!lectureId
  });

  const {
    data: assignment,
    refetch: refetchAssignment,
    isLoading: isLoadingAssignment
  } = useQuery<Assignment>({
    queryKey: ['assignment', assignmentId],
    queryFn: () => getAssignment(lectureId, assignmentId, true),
    enabled: !!lectureId && !!assignmentId
  });

  const { data: latestSubmissionsNumber = 0 } = useQuery<number>({
    queryKey: ['latestSubmissionsNumber', lectureId, assignmentId],
    queryFn: async () => {
      const submissions = await getAllSubmissions(
        lectureId,
        assignmentId,
        'latest'
      );
      return submissions.length;
    },
    enabled: !!lectureId && !!assignmentId
  });

  const { data: students = 0 } = useQuery<number>({
    queryKey: ['users', lectureId],
    queryFn: async () => {
      const users = await getUsers(lectureId);
      return users['students'].length;
    },
    enabled: !!lectureId
  });

  if (isLoadingLecture || isLoadingAssignment) {
    return (
      <div>
        <Card>
          <LinearProgress />
        </Card>
      </div>
    );
  }

  const onAssignmentChange = async () => {
    await refetchAssignment();
  };

  return (
    <Box
      sx={{
        m: 5,
        flex: 1,
        overflow: 'auto',
        display: 'flex',
        flexDirection: 'column'
      }}
    >
      <SectionTitle title={assignment.name} />
      <Box
        sx={{
          ml: 3,
          mr: 3,
          mb: 3,
          mt: 5,
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: '24px'
        }}
      >
        <Box
          sx={{
            gridColumn: 'span 2',
            flex: 2,
            display: 'flex',
            flexDirection: 'column'
          }}
        >
          <AssignmentStatus
            lecture={lecture}
            assignment={assignment}
            onAssignmentChange={onAssignmentChange}
          />
        </Box>

        <Box
          sx={{
            gridColumn: 'span 1',
            flex: 1,
            display: 'flex',
            flexDirection: 'column'
          }}
        >
          <OverviewCard
            lecture={lecture}
            assignment={assignment}
            latestSubmissions={latestSubmissionsNumber}
            students={students}
          />
        </Box>
      </Box>
    </Box>
  );
};
