/**
 * Copyright (c) 2022, TU Wien
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

import {
  IconButton,
  Card,
  LinearProgress,
  Stack,
  TableCell,
  TableRow,
  Typography,
  Tooltip,
  Alert,
  Chip
} from '@mui/material';
import * as React from 'react';
import { Assignment } from '../../model/assignment';
import { Lecture } from '../../model/lecture';
import {
  deleteAssignment,
  getAllAssignments
} from '../../services/assignments.service';
import {
  CreateDialog,
  EditLectureDialog,
  ExportGradesForLectureDialog
} from '../util/dialog';
import { getLecture, updateLecture } from '../../services/lectures.service';
import { red, grey } from '@mui/material/colors';
import { enqueueSnackbar } from 'notistack';
import { useNavigate } from 'react-router-dom';
import { ButtonTr, GraderTable } from '../util/table';
import { DeadlineComponent } from '../util/deadline';
import CloseIcon from '@mui/icons-material/Close';
import SearchIcon from '@mui/icons-material/Search';
import { showDialog } from '../util/dialog-provider';
import { updateMenus } from '../../menu';
import { extractIdsFromBreadcrumbs } from '../util/breadcrumbs';
import { useQuery } from '@tanstack/react-query';
import { AssignmentDetail } from '../../model/assignmentDetail';
import { queryClient } from '../../widgets/assignmentmanage';
import CheckIcon from '@mui/icons-material/Check';
import { GroupsDropDownMenu } from '../util/groups-drop-down-menu';
import { useState } from 'react';

interface IAssignmentTableProps {
  lecture: Lecture;
  rows: Assignment[];
  refreshAssignments: any;
}

const AssignmentTable = (props: IAssignmentTableProps) => {
  const navigate = useNavigate();
  const headers = [
    { name: 'Name' },
    { name: 'Group', width: 200 },
    { name: 'Points', width: 100 },
    { name: 'Deadline', width: 200 },
    { name: 'Status', width: 130 },
    { name: 'Show Details', width: 75 },
    { name: 'Delete Assignment', width: 100 }
  ];

  return (
    <>
      {props.rows.length === 0 ? (
        <Typography
          variant="body1"
          align="center"
          color="text.secondary"
          sx={{ mt: 2 }}
        >
          No assignments available. Please add one.
        </Typography>
      ) : (
        <GraderTable<Assignment>
          headers={headers}
          rows={props.rows}
          rowFunc={row => {
            return (
              <TableRow
                key={row.name}
                component={ButtonTr}
                onClick={() =>
                  navigate(`/lecture/${props.lecture.id}/assignment/${row.id}`)
                }
              >
                <TableCell component="th" scope="row">
                  <Typography variant={'subtitle2'} sx={{ fontSize: 16 }}>
                    {row.name}
                  </Typography>
                </TableCell>
                <TableCell align={'left'}>
                  {row.settings.group !== '' && row.settings.group !== null && (
                    <Chip
                      label={row.settings.group}
                      color={'primary'}
                      variant={'outlined'}
                    />
                  )}
                </TableCell>
                <TableCell align={'center'}>{row.points}</TableCell>
                <TableCell>
                  <DeadlineComponent
                    component={'chip'}
                    deadline={row.settings.deadline}
                    compact={true}
                  />
                </TableCell>
                <TableCell>{row.status}</TableCell>
                <TableCell>
                  <IconButton aria-label="detail view" size={'small'}>
                    <SearchIcon />
                  </IconButton>
                </TableCell>
                <TableCell>
                  <Tooltip
                    title={
                      row.status === 'released' || row.status === 'complete'
                        ? 'Released or Completed Assignments cannot be deleted'
                        : `Delete Assignment ${row.name}`
                    }
                  >
                    <span>
                      {' '}
                      {/* span because of https://mui.com/material-ui/react-tooltip/#disabled-elements */}
                      <IconButton
                        aria-label="delete assignment"
                        size={'small'}
                        disabled={
                          row.status === 'released' || row.status === 'complete'
                        }
                        onClick={e => {
                          showDialog(
                            'Delete Assignment',
                            'Do you wish to delete this assignment?',
                            async () => {
                              try {
                                await deleteAssignment(
                                  props.lecture.id,
                                  row.id
                                );
                                await updateMenus(true);
                                enqueueSnackbar(
                                  'Successfully Deleted Assignment',
                                  {
                                    variant: 'success'
                                  }
                                );
                                props.refreshAssignments();
                              } catch (error: any) {
                                enqueueSnackbar(error.message, {
                                  variant: 'error'
                                });
                              }
                            }
                          );
                          e.stopPropagation();
                        }}
                      >
                        <CloseIcon
                          sx={{
                            color:
                              row.status === 'released' ||
                              row.status === 'complete'
                                ? grey[500]
                                : red[500]
                          }}
                        />
                      </IconButton>
                    </span>
                  </Tooltip>
                </TableCell>
              </TableRow>
            );
          }}
        />
      )}
    </>
  );
};

export const LectureComponent = () => {
  const [isEditDialogOpen, setEditDialogOpen] = React.useState(false);
  const { lectureId } = extractIdsFromBreadcrumbs();
  const allGroupsValue = 'All';
  const [chosenGroup, setChosenGroup] = useState(allGroupsValue);

  const { data: lecture, refetch: refetchLecture } = useQuery<Lecture>({
    queryKey: ['lecture', lectureId],
    queryFn: () => getLecture(lectureId, true),
    enabled: true
  });

  const {
    data: assignments = [],
    isPending: isPendingAssignments,
    refetch: refreshAssignments
  } = useQuery<AssignmentDetail[]>({
    queryKey: ['assignments', lectureId],
    queryFn: () => getAllAssignments(lectureId),
    enabled: true
  });

  const handleUpdateLecture = updatedLecture => {
    updateLecture(updatedLecture).then(
      async response => {
        await updateMenus(true);
        // Invalidate query key "lectures" and "completedLectures", so that we trigger refetch on lectures table and correct lecture name is shown in the table!
        await queryClient.invalidateQueries({ queryKey: ['lectures'] });
        await queryClient.invalidateQueries({
          queryKey: ['completedLectures']
        });
        setRefreshTrigger(prev => !prev);
      },
      error => {
        enqueueSnackbar(error.message, {
          variant: 'error'
        });
      }
    );
  };

  const [refreshTrigger, setRefreshTrigger] = React.useState(false);

  React.useEffect(() => {
    refetchLecture();
  }, [refreshTrigger, refetchLecture]);

  if (isPendingAssignments) {
    return (
      <div>
        <Card>
          <LinearProgress />
        </Card>
      </div>
    );
  }

  return (
    <Stack
      direction={'column'}
      overflow={'hidden'}
      sx={{ mt: 5, ml: 5, flex: 1 }}
    >
      <Typography variant={'h4'} sx={{ mr: 2 }}>
        {lecture.name}
        {lecture.complete ? (
          <Chip
            sx={{ ml: 1 }}
            label={'Complete'}
            color="error"
            size="small"
            icon={<CheckIcon />}
          />
        ) : null}
      </Typography>
      <Stack
        direction="column"
        justifyContent="space-between"
        alignItems="left"
        sx={{ mt: 2, mb: 1 }}
      >
        <Stack direction="row" alignItems="center" sx={{ mr: 2, mb: 2 }}>
          {lecture.code === lecture.name ? (
            <Alert severity="info">
              The name of the lecture is identical to the lecture code. You
              should give it a meaningful title that accurately reflects its
              content.{' '}
              <span
                style={{
                  cursor: 'pointer',
                  textDecoration: 'underline',
                  fontWeight: 'bold'
                }}
                onClick={() => setEditDialogOpen(true)}
              >
                Rename Lecture.
              </span>
            </Alert>
          ) : null}
        </Stack>
        <Stack
          direction="row"
          justifyContent="space-between"
          alignItems="center"
          sx={{ mt: 2, mb: 1 }}
        >
          <Stack direction={'row'} spacing={2} justifyContent={'center'}>
            <Typography variant={'h6'}>Assignments</Typography>
            <GroupsDropDownMenu
              assignments={assignments}
              chosenGroup={chosenGroup}
              setChosenGroup={setChosenGroup}
              allGroupsValue={allGroupsValue}
            />
          </Stack>
          <Stack
            direction={'row'}
            alignItems="center"
            spacing={2}
            sx={{ mr: 2 }}
          >
            <CreateDialog
              lecture={lecture}
              handleSubmit={async () => {
                await refreshAssignments();
              }}
            />
            <ExportGradesForLectureDialog lecture={lecture} />
            <EditLectureDialog
              lecture={lecture}
              handleSubmit={handleUpdateLecture}
              open={isEditDialogOpen}
              handleClose={() => setEditDialogOpen(false)}
            />
          </Stack>
        </Stack>
      </Stack>
      <AssignmentTable
        lecture={lecture}
        rows={
          chosenGroup === allGroupsValue
            ? assignments
            : assignments.filter(
                assignment => assignment.settings.group === chosenGroup
              )
        }
        refreshAssignments={refreshAssignments}
      />
    </Stack>
  );
};
