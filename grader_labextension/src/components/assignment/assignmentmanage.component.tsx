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

interface ILectureTableProps {
  rows: Lecture[];
}

const LectureTable = (props: ILectureTableProps) => {
  const navigate = useNavigate();
  const headers = [
    { name: 'ID', width: 100 },
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
            <TableCell style={{ width: 100 }} component='th' scope='row'>
              {row.id}
            </TableCell>
            <TableCell>{row.name}</TableCell>
            <TableCell>{row.code}</TableCell>
          </TableRow>
        );
      }}
    />
  );
};

/**
 * Renders the lectures which the student addends.
 * @param props Props of the lecture file components
 */
export const AssignmentManageComponent = () => {
  const allLectures = useRouteLoaderData('root') as {
    lectures: Lecture[];
    completedLectures: Lecture[];
  };
  const [showComplete, setShowComplete] = useState(false);

  return (
    <Stack flexDirection={'column'} sx={{ m: 5, flex: 1, overflow: 'hidden' }}>
      <Stack direction={'row'} spacing={2}>
        <Typography variant='h6' sx={{ mb: 1 }}>
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
