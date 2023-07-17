import { Lecture } from '../../model/lecture';
import { useNavigate } from 'react-router-dom';
import * as React from 'react';
import {
  Button,
  ButtonProps,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableFooter,
  TableHead, TablePagination,
  TableRow, TableRowProps,
  Typography
} from '@mui/material';
import TablePaginationActions from '@mui/material/TablePagination/TablePaginationActions';
import { matchesAny } from 'typedoc/dist/lib/utils/paths';
import { ReactElement, ReactNode } from 'react';

export function ButtonTr({ children, ...rest }: TableRowProps & ButtonProps) {
  return (
    <Button style={{ textTransform: 'none' }} component={TableRow} {...rest}>
      {children}
    </Button>
  );
}

interface IHeaderCell {
  name: string;
  width?: number;
}

interface IGraderTableProps<T> {
  headers: IHeaderCell[];
  rows: T[];
  rowFunc: (row: T) => ReactElement;
}

export function GraderTable<T>(props: IGraderTableProps<T>) {
  const [page, setPage] = React.useState(0);
  const [rowsPerPage, setRowsPerPage] = React.useState(5);

  // Avoid a layout jump when reaching the last page with empty rows.
  const emptyRows =
    page > 0 ? Math.max(0, (1 + page) * rowsPerPage - props.rows.length) : 0;

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
            {props.headers.map(header =>
              <TableCell  style={{ width: header.width }}>
                <Typography color='primary'>{header.name}</Typography>
              </TableCell>
            )}
          </TableRow>
        </TableHead>
        <TableBody>
          {(rowsPerPage > 0
              ? props.rows.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
              : props.rows
          ).map((row) => props.rowFunc(row))}
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
              count={props.rows.length}
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