import * as React from 'react';
import { ReactElement } from 'react';
import {
  Box,
  Button,
  ButtonProps,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TableRowProps,
  Typography
} from '@mui/material';

export function ButtonTr({ children, ...rest }: TableRowProps & ButtonProps) {
  return (
    <Button style={{ textTransform: 'none' }} component={TableRow} {...rest}>
      {children}
    </Button>
  );
}

export interface IHeaderCell {
  name: string;
  width?: number;
}

export const headerWidth = (headers: IHeaderCell[], name: string) =>
  headers.find(h => h.name === name).width;

interface IGraderTableProps<T> {
  headers: IHeaderCell[];
  rows: T[];
  rowFunc: (row: T) => ReactElement;
}

export function GraderTable<T>(props: IGraderTableProps<T>) {
  return (
    <Box sx={{ flex: 1, overflow: 'scroll' }}>
      <Table aria-label="simple table" stickyHeader>
        <TableHead>
          <TableRow>
            {props.headers.map(header => (
              <TableCell style={{ width: header.width }}>
                <Typography color="primary">{header.name}</Typography>
              </TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>{props.rows.map(row => props.rowFunc(row))}</TableBody>
      </Table>
    </Box>
  );
}
