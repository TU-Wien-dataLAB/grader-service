import { Files } from './files';
import * as React from 'react';
import { Lecture } from '../../../model/lecture';
import { Assignment } from '../../../model/assignment';
import { getAssignment } from '../../../services/assignments.service';
import { useQuery } from '@tanstack/react-query';
import { extractIdsFromBreadcrumbs } from '../../util/breadcrumbs';
import { getLecture } from '../../../services/lectures.service';

export const FileView = () => {
  const { lectureId, assignmentId } = extractIdsFromBreadcrumbs();

  const { data: lectureData, isLoading: isLoadingLecture } = useQuery<Lecture>({
    queryKey: ['lecture', lectureId],
    queryFn: () => getLecture(lectureId),
    enabled: !!lectureId
  });

  const {
    data: assignmentData,
    refetch: refetchAssignment,
    isLoading: isLoadingAssignment
  } = useQuery<Assignment>({
    queryKey: ['assignment', assignmentId],
    queryFn: () => getAssignment(lectureId, assignmentId),
    enabled: !!lectureId && !!assignmentId
  });

  if (isLoadingLecture || isLoadingAssignment) {
    return <div>Loading...</div>;
  }

  const lecture = lectureData;
  const assignment = assignmentData;

  const onAssignmentChange = async () => {
    await refetchAssignment();
  };

  return (
    <Files
      lecture={lecture}
      assignment={assignment}
      onAssignmentChange={onAssignmentChange}
    />
  );
};
