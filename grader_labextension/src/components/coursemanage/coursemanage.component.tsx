// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import * as React from 'react';
import { useState } from 'react';
import { Lecture } from '../../model/lecture';
import { useNavigate, useRouteLoaderData } from 'react-router-dom';
import { FormControlLabel, FormGroup, Stack, Switch, TableCell, TableRow, Typography } from '@mui/material';
import Box from '@mui/material/Box';
import { ButtonTr, GraderTable } from '../util/table';
import { SectionTitle } from '../util/section-title';

interface ILectureTableProps {
  rows: Lecture[];
}

const LectureTable = (props: ILectureTableProps) => {
  const navigate = useNavigate();
  const headers = [
    { name: 'ID', width: 50 },
    { name: 'Name' },
    { name: 'Code' }
  ];
  return (
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
            <TableCell style={{ width: 50 }} component='th' scope='row'>
              {row.id}
            </TableCell>
            <TableCell><Typography variant={'subtitle2'} sx={{ fontSize: 16 }}>{row.name}</Typography></TableCell>
            <TableCell>{row.code}</TableCell>
          </TableRow>
        );
      }}
    />
  );
};

export const CourseManageComponent = () => {
  const allLectures = useRouteLoaderData('root') as {
    lectures: Lecture[];
    completedLectures: Lecture[];
  };
  const [showComplete, setShowComplete] = useState(false);

  return (
    <Stack direction={'column'} sx={{ m: 5, flex: 1, overflow: 'hidden' }}>
      <Stack direction='row' justifyContent='center'>
        <Typography variant={'h4'}>Course Management</Typography>
      </Stack>
      <Stack direction={'row'} justifyContent='space-between'>
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
            label='Completed Lectures'
          />
        </FormGroup>
      </Stack>

      <LectureTable
        rows={
          showComplete ? allLectures.completedLectures : allLectures.lectures
        }
      />
    </Stack>
  );
};
