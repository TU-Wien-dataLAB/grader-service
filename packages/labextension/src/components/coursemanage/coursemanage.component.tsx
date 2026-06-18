// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import * as React from 'react';
import { useState } from 'react';
import { Lecture } from '../../model/lecture';
import { useNavigate } from 'react-router-dom';
import {
  FormControlLabel,
  FormGroup,
  Stack,
  Switch,
  TableCell,
  TableRow,
  Typography
} from '@mui/material';
import { ButtonTr, GraderTable } from '../util/table';
import { getAllLectures } from '../../services/lectures.service';
import { useQuery } from '@tanstack/react-query';

interface ILectureTableProps {
  rows: Lecture[];
  completed: boolean;
}

const LectureTable = (props: ILectureTableProps) => {
  const navigate = useNavigate();
  const headers = [
    { name: 'ID', width: 50 },
    { name: 'Name' },
    { name: 'Code' }
  ];
  return (
    <>
      {props.rows.length === 0 && props.completed ? (
        <Typography
          variant="body1"
          align="center"
          color="text.secondary"
          sx={{ mt: 2 }}
        >
          No lectures are completed.
        </Typography>
      ) : props.rows.length === 0 && !props.completed ? (
        <Typography
          variant="body1"
          align="center"
          color="text.secondary"
          sx={{ mt: 2 }}
        >
          No lectures are currently active.
        </Typography>
      ) : (
        <GraderTable<Lecture>
          headers={headers}
          rows={props.rows}
          rowFunc={row => {
            return (
              <TableRow
                key={row.name}
                component={ButtonTr}
                onClick={() => navigate(`/lecture/${row.id}`)}
              >
                <TableCell style={{ width: 50 }} component="th" scope="row">
                  {row.id}
                </TableCell>
                <TableCell>
                  <Typography variant={'subtitle2'} sx={{ fontSize: 16 }}>
                    {row.name}
                  </Typography>
                </TableCell>
                <TableCell>{row.code}</TableCell>
              </TableRow>
            );
          }}
        />
      )}
    </>
  );
};

export const CourseManageComponent = () => {
  const { data: lectures, isLoading: isLoadingOngoingLectures } = useQuery<
    Lecture[]
  >({
    queryKey: ['instructorLectures'],
    queryFn: () => getAllLectures({ complete: false, instructor: true })
  });

  const { data: completedLectures, isLoading: isLoadingCompletedLectures } =
    useQuery<Lecture[]>({
      queryKey: ['instructorCompletedLectures'],
      queryFn: () => getAllLectures({ complete: true, instructor: true })
    });

  const [showComplete, setShowComplete] = useState(false);

  if (isLoadingCompletedLectures || isLoadingOngoingLectures) {
    return <div>Loading...</div>;
  }

  return (
    <Stack direction={'column'} sx={{ mt: 5, ml: 5, flex: 1 }}>
      <Stack direction="row" justifyContent="center">
        <Typography variant={'h4'}>Course Management</Typography>
      </Stack>
      <Stack direction={'row'} justifyContent="space-between">
        <Typography variant={'h6'} sx={{ mb: 1 }}>
          Lectures
        </Typography>
        <FormGroup>
          <FormControlLabel
            control={
              <Switch
                checked={showComplete}
                onChange={ev => setShowComplete(ev.target.checked)}
              />
            }
            label="Completed Lectures"
          />
        </FormGroup>
      </Stack>

      <LectureTable
        completed={showComplete}
        rows={showComplete ? completedLectures : lectures}
      />
    </Stack>
  );
};
