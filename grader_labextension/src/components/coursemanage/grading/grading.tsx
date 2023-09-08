import * as React from 'react';
import Box from '@mui/material/Box';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TablePagination from '@mui/material/TablePagination';
import TableRow from '@mui/material/TableRow';
import TableSortLabel from '@mui/material/TableSortLabel';
import Typography from '@mui/material/Typography';
import Paper from '@mui/material/Paper';
import Checkbox from '@mui/material/Checkbox';
import { visuallyHidden } from '@mui/utils';
import { Lecture } from '../../../model/lecture';
import { Assignment } from '../../../model/assignment';
import { Outlet, useNavigate, useOutletContext, useRouteLoaderData } from 'react-router-dom';
import { Submission } from '../../../model/submission';
import { utcToLocalFormat } from '../../../services/datetime.service';
import {
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  Stack,
  Toolbar,
  Tooltip
} from '@mui/material';
import { SectionTitle } from '../../util/section-title';
import { enqueueSnackbar } from 'notistack';
import { getAllSubmissions, getLogs } from '../../../services/submissions.service';
import { EnhancedTableToolbar } from './table-toolbar';
import EditNoteOutlinedIcon from '@mui/icons-material/EditNoteOutlined';
import { green } from '@mui/material/colors';
import AddIcon from '@mui/icons-material/Add';


/**
 * Calculates chip color based on submission status.
 * @param value submission status
 * @return chip color
 */
const getColor = (value: string) => {
  if (value === 'not_graded') {
    return 'warning';
  } else if (
    value === 'automatically_graded' ||
    value === 'manually_graded'
  ) {
    return 'success';
  } else if (value === 'grading_failed') {
    return 'error';
  }
  return 'primary';
};

export const getAutogradeChip = (submission: Submission) => {
  return <Chip
    sx={{ textTransform: 'capitalize' }}
    variant='outlined'
    label={submission.auto_status.split('_').join(' ')}
    color={getColor(submission.auto_status)} />;
};

export const getManualChip = (submission: Submission) => {
  return <Chip
    sx={{ textTransform: 'capitalize' }}
    variant='outlined'
    label={submission.manual_status.split('_').join(' ')}
    color={getColor(submission.manual_status)}
  />;
};

export const getFeedbackChip = (submission: Submission) => {
  return <Chip
    variant='outlined'
    label={submission.feedback_available ? 'Generated' : 'Not Generated'}
    color={submission.feedback_available ? 'success' : 'error'}
  />;
};

function descendingComparator<T>(a: T, b: T, orderBy: keyof T) {
  if (b[orderBy] < a[orderBy]) {
    return -1;
  }
  if (b[orderBy] > a[orderBy]) {
    return 1;
  }
  return 0;
}

type Order = 'asc' | 'desc';

function getComparator<Key extends keyof Submission>(
  order: Order,
  orderBy: Key
): (
  a: Submission,
  b: Submission
) => number {
  return order === 'desc'
    ? (a, b) => descendingComparator<Submission>(a, b, orderBy)
    : (a, b) => -descendingComparator<Submission>(a, b, orderBy);
}

// Since 2020 all major browsers ensure sort stability with Array.prototype.sort().
// stableSort() brings sort stability to non-modern browsers (notably IE11). If you
// only support modern browsers you can replace stableSort(exampleArray, exampleComparator)
// with exampleArray.slice().sort(exampleComparator)
function stableSort<T>(array: readonly T[], comparator: (a: T, b: T) => number) {
  const stabilizedThis = array.map((el, index) => [el, index] as [T, number]);
  stabilizedThis.sort((a, b) => {
    const order = comparator(a[0], b[0]);
    if (order !== 0) {
      return order;
    }
    return a[1] - b[1];
  });
  return stabilizedThis.map((el) => el[0]);
}

interface HeadCell {
  disablePadding: boolean;
  id: keyof Submission | 'edit';
  label: string;
  numeric: boolean;
}

const headCells: readonly HeadCell[] = [
  {
    id: 'id',
    numeric: true,
    disablePadding: true,
    label: 'ID'
  },
  {
    id: 'username',
    numeric: false,
    disablePadding: false,
    label: 'User'
  },
  {
    id: 'submitted_at',
    numeric: true,
    disablePadding: false,
    label: 'Date'
  },
  {
    id: 'auto_status',
    numeric: false,
    disablePadding: false,
    label: 'Autograde-Status'
  },
  {
    id: 'manual_status',
    numeric: false,
    disablePadding: false,
    label: 'Manualgrade-Status'
  },
  {
    id: 'feedback_available',
    numeric: false,
    disablePadding: false,
    label: 'Feedback generated'
  },
  {
    id: 'score',
    numeric: true,
    disablePadding: false,
    label: 'Score'
  },
  {
    id: 'edit',
    numeric: false,
    disablePadding: false,
    label: 'Edit'
  }
];

interface EnhancedTableProps {
  numSelected: number;
  onRequestSort: (event: React.MouseEvent<unknown>, property: keyof Submission) => void;
  onSelectAllClick: (event: React.ChangeEvent<HTMLInputElement>) => void;
  order: Order;
  orderBy: string;
  rowCount: number;
}

function EnhancedTableHead(props: EnhancedTableProps) {
  const { onSelectAllClick, order, orderBy, numSelected, rowCount, onRequestSort } =
    props;
  const createSortHandler =
    (property: keyof Submission) => (event: React.MouseEvent<unknown>) => {
      onRequestSort(event, property);
    };

  return (
    <TableHead>
      <TableRow>
        <TableCell padding='checkbox'>
          <Checkbox
            color='primary'
            indeterminate={numSelected > 0 && numSelected < rowCount}
            checked={rowCount > 0 && numSelected === rowCount}
            onChange={onSelectAllClick}
            inputProps={{
              'aria-label': 'select all desserts'
            }}
          />
        </TableCell>
        {headCells.map((headCell) => (
          <TableCell
            key={headCell.id}
            align={headCell.numeric ? 'right' : 'left'}
            padding={headCell.disablePadding ? 'none' : 'normal'}
            sortDirection={orderBy === headCell.id ? order : false}
          >
            {headCell.id !== 'edit'
              ? <TableSortLabel
                active={orderBy === headCell.id}
                direction={orderBy === headCell.id ? order : 'asc'}
                onClick={createSortHandler(headCell.id)}
              >
                {headCell.label}
                {orderBy === headCell.id ? (
                  <Box component='span' sx={visuallyHidden}>
                    {order === 'desc' ? 'sorted descending' : 'sorted ascending'}
                  </Box>
                ) : null}
              </TableSortLabel>
              : headCell.label
            }
          </TableCell>
        ))}
      </TableRow>
    </TableHead>
  );
}

export default function GradingTable() {
  const navigate = useNavigate();

  const {
    lecture,
    assignment,
    rows,
    setRows,
    manualGradeSubmission,
    setManualGradeSubmission
  } = useOutletContext() as {
    lecture: Lecture,
    assignment: Assignment,
    rows: Submission[],
    setRows: React.Dispatch<React.SetStateAction<Submission[]>>,
    manualGradeSubmission: Submission,
    setManualGradeSubmission: React.Dispatch<React.SetStateAction<Submission>>
  };

  const [order, setOrder] = React.useState<Order>('asc');
  const [orderBy, setOrderBy] = React.useState<keyof Submission>('id');
  const [selected, setSelected] = React.useState<readonly number[]>([]);
  const [page, setPage] = React.useState(0);
  const [rowsPerPage, setRowsPerPage] = React.useState(5);
  const [shownSubmissions, setShownSubmissions] = React.useState('none' as 'none' | 'latest' | 'best');

  const [showLogs, setShowLogs] = React.useState(false);
  const [logs, setLogs] = React.useState(undefined);

  /**
   * Opens log dialog which contain autograded logs from grader service.
   * @param event the click event
   * @param submissionId submission for which to show logs
   */
  const openLogs = (event: React.MouseEvent<unknown>, submissionId: number) => {
    getLogs(lecture.id, assignment.id, submissionId).then(
      logs => {
        setLogs(logs);
        setShowLogs(true);
      },
      error => {
        enqueueSnackbar('No logs for submission', {
          variant: 'error'
        });
      }
    );
    event.stopPropagation();
  };

  const updateSubmissions = (filter: 'none' | 'latest' | 'best') => {
    getAllSubmissions(lecture.id, assignment.id, filter, true, true).then(
      response => {
        setRows(response);
      }
    );
  };

  const switchShownSubmissions = (
    event: React.MouseEvent<HTMLElement>,
    value: 'none' | 'latest' | 'best'
  ) => {
    if (value !== null) {
      setShownSubmissions(value);
      updateSubmissions(value);
    } else {
      updateSubmissions(shownSubmissions); // implicit reload
    }
  };

  const handleRequestSort = (
    event: React.MouseEvent<unknown>,
    property: keyof Submission
  ) => {
    const isAsc = orderBy === property && order === 'asc';
    setOrder(isAsc ? 'desc' : 'asc');
    setOrderBy(property);
  };


  const handleSelectAllClick = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.checked) {
      const newSelected = rows.map((n) => n.id);
      setSelected(newSelected);
      return;
    }
    setSelected([]);
  };

  const handleClick = (event: React.MouseEvent<unknown>, id: number) => {
    const selectedIndex = selected.indexOf(id);
    let newSelected: readonly number[] = [];

    if (selectedIndex === -1) {
      newSelected = newSelected.concat(selected, id);
    } else if (selectedIndex === 0) {
      newSelected = newSelected.concat(selected.slice(1));
    } else if (selectedIndex === selected.length - 1) {
      newSelected = newSelected.concat(selected.slice(0, -1));
    } else if (selectedIndex > 0) {
      newSelected = newSelected.concat(
        selected.slice(0, selectedIndex),
        selected.slice(selectedIndex + 1)
      );
    }

    setSelected(newSelected);
    event.stopPropagation();
  };

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const isSelected = (id: number) => selected.indexOf(id) !== -1;

  // Avoid a layout jump when reaching the last page with empty rows.
  const emptyRows =
    page > 0 ? Math.max(0, (1 + page) * rowsPerPage - rows.length) : 0;

  const visibleRows = React.useMemo(
    () =>
      stableSort(rows, getComparator(order, orderBy)).slice(
        page * rowsPerPage,
        page * rowsPerPage + rowsPerPage
      ),
    [order, orderBy, page, rowsPerPage, rows]
  );

  return (
    <Stack sx={{ flex: 1, ml: 5, mr: 5, overflow: 'hidden' }}>
      <Stack direction={'row'} justifyContent={'flex-end'} alignItems={'center'} spacing={2} sx={{ mb: 2 }}>
        {/*
        TODO: Requires backend implementation and frontend tweaks
        <Tooltip title={'Manually add new submission'}>
             <Button onClick={(event) => {
                        event.stopPropagation();
                        navigate("create");
                      }}
                variant='outlined'
                size="small"
                sx={{ whiteSpace: 'nowrap'}}>
                <AddIcon fontSize='small' sx={{mr: 1}}/>
                New
              </Button>
          </Tooltip>
         */}
      </Stack>
      <EnhancedTableToolbar lecture={lecture} assignment={assignment} rows={rows}
                            clearSelection={() => setSelected([])} selected={selected}
                            shownSubmissions={shownSubmissions}
                            switchShownSubmissions={switchShownSubmissions} />
      <Box sx={{ flex: 1, overflow: 'scroll' }}>
        <Table
          // sx={{ minWidth: 750 }}
          aria-labelledby='tableTitle'
          stickyHeader
        >
          <EnhancedTableHead
            numSelected={selected.length}
            order={order}
            orderBy={orderBy}
            onSelectAllClick={handleSelectAllClick}
            onRequestSort={handleRequestSort}
            rowCount={rows.length}
          />
          <TableBody>
            {visibleRows.map((row, index) => {
              const isItemSelected = isSelected(row.id);
              const labelId = `enhanced-table-checkbox-${index}`;

              return (
                <TableRow
                  hover
                  onClick={(event) => {
                    setManualGradeSubmission(row);
                    navigate('manual');
                  }
                  }
                  role='button'
                  aria-checked={isItemSelected}
                  tabIndex={-1}
                  key={row.id}
                  selected={isItemSelected}
                  sx={{ cursor: 'pointer' }}
                >
                  <TableCell padding='checkbox'>
                    <Checkbox
                      color='primary'
                      checked={isItemSelected}
                      inputProps={{
                        'aria-labelledby': labelId
                      }}
                      onClick={(event) => handleClick(event, row.id)}
                    />
                  </TableCell>
                  <TableCell
                    component='th'
                    id={labelId}
                    scope='row'
                    padding='none'
                    align='right'
                  >
                    {row.id}
                  </TableCell>
                  <TableCell align='left'>{row.username}</TableCell>
                  <TableCell align='right'>{utcToLocalFormat(row.submitted_at)}</TableCell>
                  <TableCell align='left'><Chip
                    sx={{ textTransform: 'capitalize' }}
                    variant='outlined'
                    label={row.auto_status.split('_').join(' ')}
                    color={getColor(row.auto_status)}
                    clickable={true}
                    onClick={(event) => openLogs(event, row.id)}
                  /></TableCell>
                  <TableCell align='left'>{getManualChip(row)}</TableCell>
                  <TableCell align='left'>{getFeedbackChip(row)}</TableCell>
                  <TableCell align='right'>{row.score}</TableCell>
                  <TableCell style={{ width: 55 }}>
                    <IconButton aria-label='Edit' size={'small'} onClick={(event) => {
                      event.stopPropagation();
                      setManualGradeSubmission(row);
                      navigate('edit');
                    }}>
                      <EditNoteOutlinedIcon sx={{ color: green[500] }} />
                    </IconButton>
                  </TableCell>
                </TableRow>
              );
            })}
            {emptyRows > 0 && (
              <TableRow
                style={{
                  height: 53 * emptyRows
                }}

              >
                <TableCell colSpan={6} />
              </TableRow>
            )}
          </TableBody>
        </Table>
      </Box>
      <TablePagination
        rowsPerPageOptions={[5, 10, 25]}
        component='div'
        count={rows.length}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={handleChangePage}
        onRowsPerPageChange={handleChangeRowsPerPage}
      />
      <Dialog
        open={showLogs}
        onClose={() => setShowLogs(false)}
        aria-labelledby='alert-dialog-title'
        aria-describedby='alert-dialog-description'
      >
        <DialogTitle id='alert-dialog-title'>{'Logs'}</DialogTitle>
        <DialogContent>
          <Typography
            id='alert-dialog-description'
            sx={{ fontSize: 10, fontFamily: '\'Roboto Mono\', monospace' }}
          >
            {logs}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowLogs(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Stack>
  );
}

export const GradingComponent = () => {
  const { lecture, assignments, users } = useRouteLoaderData('lecture') as {
    lecture: Lecture,
    assignments: Assignment[],
    users: { instructors: string[], tutors: string[], students: string[] }
  };
  const { assignment, allSubmissions, latestSubmissions } = useRouteLoaderData('assignment') as {
    assignment: Assignment,
    allSubmissions: Submission[],
    latestSubmissions: Submission[]
  };

  const [rows, setRows] = React.useState(allSubmissions);
  const [manualGradeSubmission, setManualGradeSubmission] = React.useState(undefined as Submission);

  return <Stack direction={'column'} sx={{ flex: 1, overflow: 'hidden' }}>
    <SectionTitle title='Grading' />
    <Outlet context={{ lecture, assignment, rows, setRows, manualGradeSubmission, setManualGradeSubmission }} />
  </Stack>;
};
