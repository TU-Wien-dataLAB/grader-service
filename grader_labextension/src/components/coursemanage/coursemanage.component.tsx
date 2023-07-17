// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import * as React from 'react';
import { Lecture } from '../../model/lecture';
import { useRouteLoaderData, Link as RouterLink, useNavigate } from 'react-router-dom';
import {
  Button, ButtonProps, FormControlLabel, FormGroup,
  ListItem,
  ListItemProps,
  ListItemText,
  Paper, Stack, Switch,
  Table, TableBody, TableCell,
  TableContainer, TableFooter,
  TableHead, TablePagination,
  TableRow, TableRowProps, Typography
} from '@mui/material';
import TablePaginationActions from '@mui/material/TablePagination/TablePaginationActions';
import Box from '@mui/material/Box';
import { useState } from 'react';
import { ButtonTr, GraderTable } from '../util/table';

interface ListItemLinkProps extends ListItemProps {
  to: string;
  text: string;
}

const ListItemLink = (props: ListItemLinkProps) => {
  const { to, ...other } = props;
  return (
    <li>
      <ListItem component={RouterLink as any} to={to} {...other}>
        <ListItemText primary={props.text} />
      </ListItem>
    </li>
  );
};


interface ILectureTableProps {
  rows: Lecture[];
}

const LectureTable = (props: ILectureTableProps) => {
  const navigate = useNavigate();
  const headers = [{ name: 'ID', width: 100 }, { name: 'Name' }, { name: 'Code' }];
  return (
    <GraderTable<Lecture> headers={headers}
                          rows={props.rows}
                          rowFunc={(row) => {
                            return <TableRow
                              key={row.name}
                              component={ButtonTr}
                              onClick={() => navigate(`/lecture/${row.id}`)}
                            >
                              <TableCell style={{ width: 100 }} component='th' scope='row'>
                                {row.id}
                              </TableCell>
                              <TableCell>{row.name}</TableCell>
                              <TableCell>{row.code}</TableCell>
                            </TableRow>;
                          }}
    />
  );
};


export const CourseManageComponent = () => {
  const allLectures = useRouteLoaderData('root') as { lectures: Lecture[], completedLectures: Lecture[] };
  const [showComplete, setShowComplete] = useState(false);

  return (
    <div className='course-list'>
      <Stack direction='row' justifyContent='center'>
        <Typography variant={'h4'}>
          Course Management
        </Typography>
      </Stack>

      <Box sx={{ m: 5 }}>
        <Stack direction={'row'} justifyContent='space-between'>
          <Typography variant={'h6'} sx={{ mb: 1 }}>Lectures</Typography>
          <FormGroup>
            <FormControlLabel
              control={<Switch checked={showComplete} onChange={(ev) => setShowComplete(ev.target.checked)} />}
              label='Completed Lectures' />
          </FormGroup>
        </Stack>

        <LectureTable rows={showComplete ? allLectures.completedLectures : allLectures.lectures} />
      </Box>
    </div>
  );
};
