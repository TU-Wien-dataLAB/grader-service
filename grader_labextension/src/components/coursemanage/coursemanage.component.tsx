// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import * as React from 'react';
import { Lecture } from '../../model/lecture';
import { useRouteLoaderData, useNavigate } from 'react-router-dom';
import {
  Button, ButtonProps, FormControlLabel, FormGroup,
  Paper, Stack, Switch,
  Table, TableBody, TableCell,
  TableContainer, TableFooter,
  TableHead, TablePagination,
  TableRow, TableRowProps, Typography,
} from '@mui/material';
import TablePaginationActions from '@mui/material/TablePagination/TablePaginationActions';
import Box from '@mui/material/Box';
import { useState } from 'react';

export interface ICourseManageProps {
  // lectures: Array<Lecture>;
  root: HTMLElement;
}

function ButtonTr({ children, ...rest }: TableRowProps & ButtonProps) {
  return (
    <Button style={{ textTransform: 'none' }} component={TableRow} {...rest}>
      {children}
    </Button>
  );
}

interface ILectureTableProps {
  rows: Lecture[];
}

export const LectureTable = (props: ILectureTableProps) => {
  const navigate = useNavigate();
  const rows = props.rows;
  const [page, setPage] = React.useState(0);
  const [rowsPerPage, setRowsPerPage] = React.useState(5);

  // Avoid a layout jump when reaching the last page with empty rows.
  const emptyRows =
    page > 0 ? Math.max(0, (1 + page) * rowsPerPage - rows.length) : 0;

  const handleChangePage = (
    event: React.MouseEvent<HTMLButtonElement> | null,
    newPage: number
  ) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (
    event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  
  return (
    <TableContainer component={Paper}>
      <Table aria-label='simple table'>
        <TableHead>
          <TableRow>
            <TableCell style={{ width: 100 }}>
              <Typography color='primary'>ID</Typography>
            </TableCell>
            <TableCell>
              <Typography color='primary'>Name</Typography>
            </TableCell>
            <TableCell>
              <Typography color='primary'>Code</Typography>
            </TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {(rowsPerPage > 0
              ? rows.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
              : rows
          ).map((row) => (
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
          ))}
          {emptyRows > 0 && (
            <TableRow style={{ height: 53 * emptyRows }}>
              <TableCell colSpan={6} />
            </TableRow>
          )}
        </TableBody>
        <TableFooter>
          <TableRow>
            <TablePagination
              rowsPerPageOptions={[5, 10]}
              count={rows.length}
              rowsPerPage={rowsPerPage}
              page={page}
              SelectProps={{
                inputProps: {
                  'aria-label': 'rows per page'
                }
              }}
              onPageChange={handleChangePage}
              onRowsPerPageChange={handleChangeRowsPerPage}
              ActionsComponent={TablePaginationActions}
            />
          </TableRow>
        </TableFooter>
      </Table>
    </TableContainer>
  );
};


export const CourseManageComponent = () => {
  const allLectures = useRouteLoaderData('root') as { lectures: Lecture[], completedLectures: Lecture[] };
  const [showComplete, setShowComplete] = useState(false);

  const [tab, setTab] = useState(0)
  const handleChange = (event: React.SyntheticEvent, newValue: number) => {
    setTab(newValue);
  };

  return (
    <div>
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
