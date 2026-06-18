import * as React from 'react';
import Box from '@mui/material/Box';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableHead from '@mui/material/TableHead';
import TablePagination from '@mui/material/TablePagination';
import TableRow from '@mui/material/TableRow';
import TableSortLabel from '@mui/material/TableSortLabel';
import Checkbox from '@mui/material/Checkbox';
import { visuallyHidden } from '@mui/utils';
import { Lecture } from '../../../model/lecture';
import { Assignment } from '../../../model/assignment';
import { Link, Outlet, useNavigate, useOutletContext } from 'react-router-dom';
import { Submission } from '../../../model/submission';
import { utcToLocalFormat } from '../../../services/datetime.service';
import { Button, Chip, IconButton, Stack, Tooltip } from '@mui/material';
import { SectionTitle } from '../../util/section-title';
import { getAllSubmissions } from '../../../services/submissions.service';
import { EnhancedTableToolbar } from './table-toolbar';
import EditNoteOutlinedIcon from '@mui/icons-material/EditNoteOutlined';
import { green } from '@mui/material/colors';
import {
  loadNumber,
  loadString,
  storeNumber,
  storeString
} from '../../../services/storage.service';
import { getAssignment } from '../../../services/assignments.service';
import { useQuery } from '@tanstack/react-query';
import { getLecture } from '../../../services/lectures.service';
import { extractIdsFromBreadcrumbs } from '../../util/breadcrumbs';
import { SubmissionLogs } from '../../util/submission-logs';
import AddIcon from '@mui/icons-material/Add';
import { ManualStatus } from '../../../model/manualStatus';
import { AutoStatus } from '../../../model/autoStatus';
import { FeedbackStatus } from '../../../model/feedbackStatus';

/**
 * Calculates chip color based on submission status.
 * @param value submission status
 * @return chip color
 */
const getColor = (value: string) => {
  if (
    value === AutoStatus.NotGraded.valueOf() ||
    value === ManualStatus.NotGraded.valueOf() ||
    value === FeedbackStatus.NotGenerated.valueOf() ||
    value === FeedbackStatus.FeedbackOutdated.valueOf()
  ) {
    return 'warning';
  } else if (
    value === AutoStatus.AutomaticallyGraded.valueOf() ||
    value === ManualStatus.ManuallyGraded.valueOf() ||
    value === FeedbackStatus.Generated.valueOf()
  ) {
    return 'success';
  } else if (
    value === AutoStatus.GradingFailed.valueOf() ||
    value === FeedbackStatus.GenerationFailed.valueOf()
  ) {
    return 'error';
  }
  return 'primary';
};

export const getAutogradeChip = (submission: Submission) => {
  return (
    <Chip
      sx={{ textTransform: 'capitalize' }}
      variant="outlined"
      label={submission.auto_status.split('_').join(' ')}
      color={getColor(submission.auto_status)}
    />
  );
};

export const getManualChip = (submission: Submission) => {
  return (
    <Chip
      sx={{ textTransform: 'capitalize' }}
      variant="outlined"
      label={submission.manual_status.split('_').join(' ')}
      color={getColor(submission.manual_status)}
    />
  );
};

export const getFeedbackChip = (submission: Submission) => {
  return (
    <Chip
      sx={{ textTransform: 'capitalize' }}
      variant="outlined"
      label={submission.feedback_status.split('_').join(' ')}
      color={getColor(submission.feedback_status)}
    />
  );
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
): (a: Submission, b: Submission) => number {
  return order === 'desc'
    ? (a, b) => descendingComparator<Submission>(a, b, orderBy)
    : (a, b) => -descendingComparator<Submission>(a, b, orderBy);
}

// Since 2020 all major browsers ensure sort stability with Array.prototype.sort().
// stableSort() brings sort stability to non-modern browsers (notably IE11). If you
// only support modern browsers you can replace stableSort(exampleArray, exampleComparator)
// with exampleArray.slice().sort(exampleComparator)
function stableSort<T>(
  array: readonly T[],
  comparator: (a: T, b: T) => number
) {
  const stabilizedThis = array.map((el, index) => [el, index] as [T, number]);
  stabilizedThis.sort((a, b) => {
    const order = comparator(a[0], b[0]);
    if (order !== 0) {
      return order;
    }
    return a[1] - b[1];
  });
  return stabilizedThis.map(el => el[0]);
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
    id: 'user_display_name',
    numeric: true,
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
    id: 'feedback_status',
    numeric: false,
    disablePadding: false,
    label: 'Feedback-Status'
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
  onRequestSort: (
    event: React.MouseEvent<unknown>,
    property: keyof Submission
  ) => void;
  onSelectAllClick: (event: React.ChangeEvent<HTMLInputElement>) => void;
  order: Order;
  orderBy: string;
  rowCount: number;
}

function EnhancedTableHead(props: EnhancedTableProps) {
  const {
    onSelectAllClick,
    order,
    orderBy,
    numSelected,
    rowCount,
    onRequestSort
  } = props;
  const createSortHandler =
    (property: keyof Submission) => (event: React.MouseEvent<unknown>) => {
      onRequestSort(event, property);
    };

  return (
    <TableHead>
      <TableRow>
        <TableCell padding="checkbox">
          <Checkbox
            color="primary"
            indeterminate={numSelected > 0 && numSelected < rowCount}
            checked={rowCount > 0 && numSelected === rowCount}
            onChange={onSelectAllClick}
            inputProps={{
              'aria-label': 'select all desserts'
            }}
          />
        </TableCell>
        {headCells.map(headCell => (
          <TableCell
            key={headCell.id}
            align={headCell.numeric ? 'right' : 'left'}
            padding={headCell.disablePadding ? 'none' : 'normal'}
            sortDirection={orderBy === headCell.id ? order : false}
          >
            {headCell.id !== 'edit' ? (
              <TableSortLabel
                active={orderBy === headCell.id}
                direction={orderBy === headCell.id ? order : 'asc'}
                onClick={createSortHandler(headCell.id)}
              >
                {headCell.label}
                {orderBy === headCell.id ? (
                  <Box component="span" sx={visuallyHidden}>
                    {order === 'desc'
                      ? 'sorted descending'
                      : 'sorted ascending'}
                  </Box>
                ) : null}
              </TableSortLabel>
            ) : (
              headCell.label
            )}
          </TableCell>
        ))}
      </TableRow>
    </TableHead>
  );
}

export default function GradingTable() {
  const navigate = useNavigate();

  const { lecture, assignment, rows, setRows, setManualGradeSubmission } =
    useOutletContext() as {
      lecture: Lecture;
      assignment: Assignment;
      rows: Submission[];
      setRows: React.Dispatch<React.SetStateAction<Submission[]>>;
      manualGradeSubmission: Submission;
      setManualGradeSubmission: React.Dispatch<
        React.SetStateAction<Submission>
      >;
    };

  const [order, setOrder] = React.useState<Order>(() => {
    const savedOrder = loadString('order');
    return savedOrder === 'asc' || savedOrder === 'desc' ? savedOrder : 'asc';
  });
  const [orderBy, setOrderBy] = React.useState<keyof Submission>(() => {
    return (loadString('grader-order-by') as keyof Submission) || 'id';
  });
  const [selected, setSelected] = React.useState<readonly number[]>([]);
  const [page, setPage] = React.useState(loadNumber('grader-page') || 0);
  const [rowsPerPage, setRowsPerPage] = React.useState(
    loadNumber('grading-rows-per-page') || 10
  );
  const [shownSubmissions, setShownSubmissions] = React.useState(
    (loadString('grading-shown-submissions') || 'none') as
      | 'none'
      | 'latest'
      | 'best'
  );

  const [search, setSearch] = React.useState(
    loadString(`grader-search-${assignment.id}`) || ''
  );

  const tableContainerRef = React.useRef<HTMLDivElement>(null); // track the table container

  React.useEffect(() => {
    storeString(`grader-search-${assignment.id}`, search);
    updateSubmissions(shownSubmissions);
    if (tableContainerRef.current) {
      tableContainerRef.current.scrollTop =
        loadNumber('table-scroll-position') || 0;
    }
  }, []);

  const [open, setOpen] = React.useState(false);
  const [submissionId, setSubmissionId] = React.useState<number | null>(null);
  const handleOpenLogs = (event: React.MouseEvent<unknown>, id: number) => {
    setSubmissionId(id);
    setOpen(true);
  };
  const handleCloseLogs = () => {
    setSubmissionId(null);
    setOpen(false);
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
      storeString('grading-shown-submissions', value);
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
    storeString('order', isAsc ? 'desc' : 'asc');
    setOrderBy(property);
    storeString('grader-order-by', property as string);
  };

  const handleSelectAllClick = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.checked) {
      const newSelected = rows.map(n => n.id);
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
    storeNumber('grader-page', newPage);
  };

  const handleChangeRowsPerPage = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const n = parseInt(event.target.value, 10);
    setRowsPerPage(n);
    storeNumber('grading-rows-per-page', n);
    setPage(0);
    storeNumber('grader-page', 0);
  };

  const isSelected = (id: number) => selected.indexOf(id) !== -1;

  // Avoid a layout jump when reaching the last page with empty rows.
  const emptyRows =
    page > 0 ? Math.max(0, (1 + page) * rowsPerPage - rows.length) : 0;

  const submissionString = (s: Submission): string => {
    return `${s.id} ${s.user_display_name} ${utcToLocalFormat(
      s.submitted_at
    )} ${s.auto_status.split('_').join(' ')} ${s.manual_status
      .split('_')
      .join(' ')} ${s.feedback_status.split('_').join(' ')} ${
      s.score
    }`.toLowerCase();
  };

  const filteredRows = React.useMemo(() => {
    return rows.filter(r => submissionString(r).includes(search));
  }, [search, rows]);

  const visibleRows = React.useMemo(
    () =>
      stableSort(filteredRows, getComparator(order, orderBy)).slice(
        page * rowsPerPage,
        page * rowsPerPage + rowsPerPage
      ),
    [order, orderBy, page, rowsPerPage, rows, search]
  );

  return (
    <Stack sx={{ flex: 1, ml: 5, mr: 5, overflow: 'hidden' }}>
      <Box ref={tableContainerRef} sx={{ flex: 1, overflow: 'auto' }}>
        <EnhancedTableToolbar
          lecture={lecture}
          assignment={assignment}
          rows={rows}
          clearSelection={() => setSelected([])}
          selected={selected}
          shownSubmissions={shownSubmissions}
          switchShownSubmissions={switchShownSubmissions}
          setSearch={setSearch}
        />
        <Table aria-labelledby="tableTitle" stickyHeader>
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
                  onClick={() => {
                    if (tableContainerRef.current) {
                      storeNumber(
                        'table-scroll-position',
                        tableContainerRef.current.scrollTop
                      ); // Save scroll position
                    }
                    setManualGradeSubmission(row);
                    navigate('manual');
                  }}
                  role="button"
                  aria-checked={isItemSelected}
                  tabIndex={-1}
                  key={row.id}
                  selected={isItemSelected}
                  sx={{ cursor: 'pointer' }}
                >
                  <TableCell padding="checkbox">
                    <Checkbox
                      color="primary"
                      checked={isItemSelected}
                      inputProps={{
                        'aria-labelledby': labelId
                      }}
                      onClick={event => handleClick(event, row.id)}
                    />
                  </TableCell>
                  <TableCell
                    component="th"
                    id={labelId}
                    scope="row"
                    padding="none"
                    align="right"
                  >
                    {row.id}
                  </TableCell>
                  <TableCell align="left">{row.user_display_name}</TableCell>
                  <TableCell align="right">
                    {utcToLocalFormat(row.submitted_at)}
                  </TableCell>
                  <TableCell align="left">
                    <Chip
                      sx={{ textTransform: 'capitalize' }}
                      variant="outlined"
                      label={row.auto_status.split('_').join(' ')}
                      color={getColor(row.auto_status)}
                      clickable={true}
                      onClick={event => {
                        event.stopPropagation(); // prevents the event from bubbling up to the TableRow
                        handleOpenLogs(event, row.id);
                      }}
                    />
                  </TableCell>
                  <TableCell align="left">{getManualChip(row)}</TableCell>
                  <TableCell align="left">{getFeedbackChip(row)}</TableCell>
                  <TableCell align="right">{row.score}</TableCell>
                  <TableCell style={{ width: 55 }}>
                    <IconButton
                      aria-label="Edit"
                      size={'small'}
                      onClick={event => {
                        event.stopPropagation();
                        setManualGradeSubmission(row);
                        navigate('edit');
                      }}
                    >
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
        {submissionId && (
          <SubmissionLogs
            lectureId={lecture.id}
            assignmentId={assignment.id}
            submissionId={submissionId}
            open={open}
            onClose={handleCloseLogs}
          />
        )}
      </Box>
      <TablePagination
        rowsPerPageOptions={[10, 25, 50]}
        component="div"
        count={filteredRows.length}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={handleChangePage}
        onRowsPerPageChange={handleChangeRowsPerPage}
      />
    </Stack>
  );
}

export const GradingComponent = () => {
  const { lectureId, assignmentId } = extractIdsFromBreadcrumbs();
  const [rows, setRows] = React.useState<Submission[]>([]);
  const [manualGradeSubmission, setManualGradeSubmission] = React.useState<
    Submission | undefined
  >(undefined);

  const { data: lectureData, isLoading: isLoadingLecture } = useQuery<Lecture>({
    queryKey: ['lecture', lectureId],
    queryFn: () => getLecture(lectureId),
    enabled: !!lectureId
  });

  const { data: assignmentData, isLoading: isLoadingAssignment } =
    useQuery<Assignment>({
      queryKey: ['assignment', assignmentId],
      queryFn: () => getAssignment(lectureId, assignmentId),
      enabled: !!lectureId && !!assignmentId
    });

  if (isLoadingLecture || isLoadingAssignment) {
    return <div>Loading...</div>;
  }

  const lecture = lectureData;
  const assignment = assignmentData;
  const submissionsLink = `/lecture/${lecture.id}/assignment/${assignment.id}/submissions`;

  return (
    <Stack direction={'column'} sx={{ flex: 1, overflow: 'hidden' }}>
      <Stack
        direction={'row'}
        justifyContent={'space-between'}
        alignItems={'center'}
        sx={{ m: 2 }}
      >
        <SectionTitle title="Grading" />
        <Tooltip title={'Make submissions for students manually'}>
          <Button
            variant="outlined"
            startIcon={<AddIcon />}
            component={Link as any}
            to={submissionsLink + '/create'}
          >
            New Submission
          </Button>
        </Tooltip>
      </Stack>
      <Outlet
        context={{
          lecture,
          assignment,
          rows,
          setRows,
          manualGradeSubmission,
          setManualGradeSubmission
        }}
      />
    </Stack>
  );
};
