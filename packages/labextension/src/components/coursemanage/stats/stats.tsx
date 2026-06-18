import { Lecture } from '../../../model/lecture';
import { Assignment } from '../../../model/assignment';
import { Submission } from '../../../model/submission';
import { Box, Card, IconButton, LinearProgress, Tooltip } from '@mui/material';
import { SectionTitle } from '../../util/section-title';
import ReplayIcon from '@mui/icons-material/Replay';
import * as React from 'react';
import { getAllSubmissions } from '../../../services/submissions.service';
import { SubmissionTimeSeries } from './submission-timeseries';
import { GradingProgress } from './grading-progress';
import { StudentSubmissions } from './student-submissions';
import { ScoreDistribution } from './score-distribution';
import { getLecture, getUsers } from '../../../services/lectures.service';
import { GradeBook } from '../../../services/gradebook';
import { AssignmentScore } from './assignment-score';
import {
  getAssignment,
  getAssignmentProperties
} from '../../../services/assignments.service';
import { extractIdsFromBreadcrumbs } from '../../util/breadcrumbs';
import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { User } from '../../../model/user';

export const filterUserSubmissions = (
  submissions: Submission[],
  users: User[]
): Submission[] => {
  return submissions.filter(
    (v, i, a) => !users.map(u => u.id).includes(v.user_id)
  );
};

export interface IStatsSubComponentProps {
  lecture: Lecture;
  assignment: Assignment;
  allSubmissions: Submission[];
  latestSubmissions: Submission[];
  users: { students: User[]; tutors: User[]; instructors: User[] };
}

export const StatsComponent = () => {
  const { lectureId, assignmentId } = extractIdsFromBreadcrumbs();

  const [allSubmissionsState, setAllSubmissionsState] = useState([]);
  const [latestSubmissionsState, setLatestSubmissionsState] = useState([]);
  const [usersState, setUsersState] = useState({
    students: [],
    tutors: [],
    instructors: []
  });
  const [gb, setGb] = React.useState(null);

  const { data: lecture, isLoading: isLoadingLecture } = useQuery({
    queryKey: ['lecture', lectureId],
    queryFn: () => getLecture(lectureId),
    enabled: !!lectureId
  });

  const { data: assignment, isLoading: isLoadingAssignment } = useQuery({
    queryKey: ['assignment', assignmentId],
    queryFn: () => getAssignment(lectureId, assignmentId),
    enabled: !!lectureId && !!assignmentId
  });

  const updateData = () => {
    getAllSubmissions(lectureId, assignmentId, 'none', true, false).then(data =>
      setAllSubmissionsState(data)
    );

    getAllSubmissions(lectureId, assignmentId, 'latest', true, false).then(
      data => setLatestSubmissionsState(data)
    );
    getUsers(lectureId).then(data => setUsersState(data));

    getAssignmentProperties(lectureId, assignmentId).then(properties => {
      setGb(new GradeBook(properties));
    });
  };

  React.useEffect(() => {
    updateData();
  }, [lecture, assignment]);

  if (isLoadingLecture || isLoadingAssignment) {
    return (
      <div>
        <Card>
          <LinearProgress />
        </Card>
      </div>
    );
  }

  return (
    <Box
      sx={{
        flex: 1,
        overflow: 'auto',
        display: 'flex',
        flexDirection: 'column'
      }}
    >
      <SectionTitle title={`${assignment.name} Stats`}>
        <Box sx={{ ml: 2 }} display="inline-block">
          <Tooltip title="Reload">
            <IconButton aria-label="reload" onClick={updateData}>
              <ReplayIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </SectionTitle>
      <Box
        sx={{
          ml: 3,
          mr: 3,
          mb: 3,
          mt: 3,
          display: 'grid',
          gridTemplateColumns: '1fr',
          gap: '24px'
        }}
      >
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            gridColumn: '1 / -1'
          }}
        >
          <SubmissionTimeSeries
            lecture={lecture}
            assignment={assignment}
            allSubmissions={allSubmissionsState}
            latestSubmissions={latestSubmissionsState}
            users={usersState}
          />
        </Box>

        <Box
          sx={{
            display: 'flex',
            gap: '24px',
            flexWrap: 'wrap'
          }}
        >
          <Box
            sx={{
              flex: '1 1 calc(33.333% - 24px)',
              minWidth: '300px'
            }}
          >
            <GradingProgress
              lecture={lecture}
              assignment={assignment}
              allSubmissions={allSubmissionsState}
              latestSubmissions={latestSubmissionsState}
              users={usersState}
            />
          </Box>
          <Box
            sx={{
              flex: '1 1 calc(33.333% - 24px)',
              minWidth: '300px'
            }}
          >
            <StudentSubmissions
              lecture={lecture}
              assignment={assignment}
              allSubmissions={allSubmissionsState}
              latestSubmissions={latestSubmissionsState}
              users={usersState}
            />
          </Box>
          <Box
            sx={{
              flex: '1 1 calc(33.333% - 24px)',
              minWidth: '300px'
            }}
          >
            <AssignmentScore gb={gb} />
          </Box>
        </Box>

        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            gridColumn: '1 / -1'
          }}
        >
          <ScoreDistribution
            lecture={lecture}
            assignment={assignment}
            allSubmissions={allSubmissionsState}
            latestSubmissions={latestSubmissionsState}
            users={usersState}
          />
        </Box>
      </Box>
    </Box>
  );
};
