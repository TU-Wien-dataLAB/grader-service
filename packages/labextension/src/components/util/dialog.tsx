// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import * as React from 'react';
import { useFormik } from 'formik';
import * as yup from 'yup';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFnsV3';
import { DateTimePicker } from '@mui/x-date-pickers';
import {
  Button,
  TextField,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Stack,
  IconButton,
  Checkbox,
  FormControlLabel,
  InputLabel,
  Select,
  MenuItem,
  Tooltip,
  Card,
  CardActionArea,
  Box,
  TooltipProps,
  tooltipClasses,
  Typography,
  Snackbar,
  Modal,
  Alert,
  AlertTitle,
  FormControl,
  Switch
} from '@mui/material';
import { Assignment } from '../../model/assignment';
import KeyboardArrowRightIcon from '@mui/icons-material/KeyboardArrowRight';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import SettingsIcon from '@mui/icons-material/Settings';
import {
  createAssignment,
  updateAssignment
} from '../../services/assignments.service';
import { Lecture } from '../../model/lecture';
import AutogradeTypeEnum = AssignmentSettings.AutogradeTypeEnum;
import HelpOutlineOutlinedIcon from '@mui/icons-material/HelpOutlineOutlined';
import AddIcon from '@mui/icons-material/Add';
import { enqueueSnackbar } from 'notistack';
import { showDialog } from './dialog-provider';
import styled from '@mui/system/styled';
import MuiAlert, { AlertProps } from '@mui/material/Alert';
import { updateMenus } from '../../menu';
import { GraderLoadingButton } from './loading-button';
import { FilesList } from './file-list';
import {
  extractRelativePaths,
  getFiles,
  lectureBasePath,
  openFile
} from '../../services/file.service';
import InfoIcon from '@mui/icons-material/Info';
import { queryClient } from '../../widgets/assignmentmanage';
import { getAllLectureSubmissions } from '../../services/lectures.service';
import FileUploadIcon from '@mui/icons-material/FileUpload';
import { ltiSyncSubmissions } from '../../services/submissions.service';
import CloudSyncIcon from '@mui/icons-material/CloudSync';
import { openBrowser } from '../coursemanage/overview/util';
import { AssignmentSettings } from '../../model/assignmentSettings';
import { TooltipComponent } from './tooltip';
import { useQuery } from '@tanstack/react-query';

const gradingBehaviourHelp = `Specifies the behaviour when a students submits an assignment.\n
No Automatic Grading: No action is taken on submit.\n
Automatic Grading: The assignment is being autograded as soon as the students makes a submission.\n
Fully Automatic Grading: The assignment is autograded and feedback is generated as soon as the student makes a submission.
(requires all scores to be based on autograde results)`;

const groupFeatureDescription = `By entering a group name, you can visually group assignments \n
based on specific topics (e.g., Assignments 1 and 2 are in "Chapter Variables", Assignment 3 in "Track AI" etc.)`;

const recalculateScoreExplaination =
  'Using this action will result in the recalculation of all submission scores \n based on the deadline/late submission settings.';

const validationSchema = yup.object({
  name: yup
    .string()
    .min(4, 'Name should be 4-50 character length')
    .max(50, 'Name should be 4-50 character length')
    .required('Name is required'),
  deadline: yup
    .date()
    .min(new Date(), 'Deadline must be set in the future')
    .nullable(),
  type: yup.mixed().oneOf(['user', 'group']),
  automatic_grading: yup.mixed().oneOf(['unassisted', 'auto', 'full_auto']),
  max_submissions: yup
    .number()
    .nullable()
    .min(1, 'Students must be able to at least submit once')
});

const validationSchemaLecture = yup.object({
  name: yup
    .string()
    .min(4, 'Name should be 4-50 characters long')
    .max(50, 'Name should be 4-50 characters long')
    .required('Name is required'),
  complete: yup.boolean()
});

export interface IEditLectureProps {
  lecture: Lecture;
  handleSubmit: (updatedLecture: Lecture) => void;
  open: boolean;
  handleClose: () => void;
}

const EditLectureNameTooltip = styled(
  ({ className, ...props }: TooltipProps) => (
    <Tooltip {...props} classes={{ popper: className }} />
  )
)(({ theme }) => ({
  [`& .${tooltipClasses.tooltip}`]: {
    maxWidth: 220
  }
}));

export const SaveAssignmentSettingsDialog = props => {
  const formik = useFormik({
    initialValues: {
      recalcScores: false
    },
    onSubmit: values => {
      updateAssignment(
        props.lecture.id,
        props.assignment,
        values.recalcScores
      ).then(
        async () => {
          await updateMenus(true);
          await queryClient.invalidateQueries({ queryKey: ['assignments'] });
          await queryClient.invalidateQueries({
            queryKey: ['assignment', props.assignment.id]
          });
          enqueueSnackbar('Successfully Updated Assignment', {
            variant: 'success'
          });
        },
        (error: Error) => {
          enqueueSnackbar(error.message, {
            variant: 'error'
          });
        }
      );
      props.setOpen(false);
    }
  });
  return (
    <Dialog
      open={props.open}
      onClose={() => {
        props.setOpen(false);
      }}
      fullWidth
      maxWidth="sm"
    >
      <DialogTitle>Save Assignment Settings</DialogTitle>
      <form onSubmit={formik.handleSubmit}>
        <DialogContent>
          <Stack spacing={0.5} direction="row" useFlexGap>
            <Checkbox
              checked={formik.values.recalcScores}
              onChange={e => {
                formik.setFieldValue('recalcScores', e.target.checked);
              }}
            />
            <Typography sx={{ pt: '9px' }}>Recalculate scores</Typography>
            <TooltipComponent
              title={recalculateScoreExplaination}
              sx={{ mt: '9px' }}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button
            color="primary"
            variant="outlined"
            onClick={() => {
              props.setOpen(false);
            }}
          >
            Cancel
          </Button>
          <Button color="primary" variant="contained" type="submit">
            Save
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

export const EditLectureDialog = (props: IEditLectureProps) => {
  const formik = useFormik({
    initialValues: {
      name: props.lecture.name,
      active: !props.lecture.complete
    },
    validationSchema: validationSchemaLecture,
    onSubmit: values => {
      const updatedLecture: Lecture = {
        ...props.lecture,
        ...values,
        complete: !values.active
      };
      props.handleSubmit(updatedLecture);
      setOpen(false);
    }
  });

  const { open, handleClose } = props;
  const [openDialog, setOpen] = React.useState(false);

  const openDialogFunction = () => {
    setOpen(true);
  };

  return (
    <div>
      <EditLectureNameTooltip
        title={
          props.lecture.code === props.lecture.name ? (
            <>
              <Typography color="inherit">Edit Lecture</Typography>
              <em>
                "Lecture name matches the code. Consider making it more
                descriptive."
              </em>
            </>
          ) : (
            'Edit Lecture'
          )
        }
      >
        <IconButton
          onClick={e => {
            e.stopPropagation();
            openDialogFunction();
          }}
          aria-label="edit"
        >
          <SettingsIcon />
        </IconButton>
      </EditLectureNameTooltip>

      <Dialog
        open={open || openDialog}
        onClose={() => {
          setOpen(false);
          handleClose();
        }}
        fullWidth
        maxWidth="sm"
      >
        <DialogTitle>Edit Lecture</DialogTitle>
        <form onSubmit={formik.handleSubmit}>
          <DialogContent>
            <Stack spacing={4}>
              <Stack spacing={1}>
                <Typography variant="subtitle1" fontWeight="bold">
                  Rename Lecture
                </Typography>
                <TextField
                  variant="outlined"
                  fullWidth
                  id="name"
                  name="name"
                  label="Lecture Name"
                  value={formik.values.name}
                  onChange={formik.handleChange}
                  error={formik.touched.name && Boolean(formik.errors.name)}
                  helperText={formik.touched.name && formik.errors.name}
                />
                {props.lecture.code === props.lecture.name && (
                  <Typography variant="body2" color="text.secondary">
                    The current name matches the lecture code. Consider updating
                    it to something more descriptive.
                  </Typography>
                )}
              </Stack>

              <Stack spacing={1}>
                <Typography variant="subtitle1" fontWeight="bold">
                  Lecture Status
                </Typography>
                <FormControlLabel
                  control={
                    <Switch
                      checked={formik.values.active}
                      onChange={e => {
                        formik.setFieldValue('active', e.target.checked);
                      }}
                      sx={{
                        '& .MuiSwitch-switchBase.Mui-checked': {
                          color: formik.values.active
                            ? 'primary.main'
                            : 'error.main'
                        },
                        '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track':
                          {
                            backgroundColor: formik.values.active
                              ? 'primary.main'
                              : 'error.main'
                          },
                        '& .MuiSwitch-switchBase': {
                          color: !formik.values.active
                            ? 'error.main'
                            : undefined
                        },
                        '& .MuiSwitch-track': {
                          backgroundColor: !formik.values.active
                            ? 'error.main'
                            : undefined
                        }
                      }}
                    />
                  }
                  label={
                    formik.values.active
                      ? 'Lecture is Active'
                      : 'Lecture is Complete'
                  }
                />
                <Typography variant="body2" color="text.secondary">
                  {formik.values.active
                    ? 'This lecture is live, and students can actively participate in it.'
                    : "This lecture is inactive and removed from your and your students' active lectures list."}
                </Typography>
              </Stack>
            </Stack>
          </DialogContent>
          <DialogActions>
            <Button
              color="primary"
              variant="outlined"
              onClick={() => {
                setOpen(false);
                handleClose();
              }}
            >
              Cancel
            </Button>
            <Button color="primary" variant="contained" type="submit">
              Save
            </Button>
          </DialogActions>
        </form>
      </Dialog>
    </div>
  );
};

interface INewAssignmentCardProps {
  onClick: React.MouseEventHandler<HTMLButtonElement>;
}

export default function NewAssignmentCard(props: INewAssignmentCardProps) {
  return (
    <Card
      sx={{ width: 225, height: '100%', m: 1.5, backgroundColor: '#fcfcfc' }}
    >
      <Tooltip title={'New Assignment'}>
        <CardActionArea
          onClick={props.onClick}
          sx={{
            width: '100%',
            height: '100%',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center'
          }}
        >
          <AddIcon sx={{ fontSize: 50 }} color="disabled" />
        </CardActionArea>
      </Tooltip>
    </Card>
  );
}

interface ICreateDialogProps {
  lecture: Lecture;
  handleSubmit: (assigment: Assignment) => void;
}

export const CreateDialog = (props: ICreateDialogProps) => {
  const formik = useFormik({
    initialValues: {
      name: 'Assignment',
      group: '',
      deadline: null,
      autograde_type: 'auto' as AutogradeTypeEnum,
      max_submissions: undefined as number
    },
    validationSchema: validationSchema,
    onSubmit: values => {
      if (
        values.max_submissions !== null &&
        values.max_submissions !== undefined
      ) {
        values.max_submissions = +values.max_submissions;
      }
      const newAssignment: Assignment = {
        name: values.name,
        status: 'created',
        settings: {
          group: values.group,
          allowed_files: [],
          deadline: values.deadline,
          max_submissions: values.max_submissions,
          autograde_type: values.autograde_type as AutogradeTypeEnum
        }
      };
      createAssignment(props.lecture.id, newAssignment).then(
        async a => {
          await updateMenus(true);
          props.handleSubmit(a);
          await queryClient.invalidateQueries({ queryKey: ['assignments'] });
        },

        error => {
          enqueueSnackbar(error.message, {
            variant: 'error'
          });
        }
      );
      setOpen(false);
    }
  });

  const [openDialog, setOpen] = React.useState(false);

  const [openSnackbar, setOpenSnackBar] = React.useState(false);

  const handleOpenSnackBar = () => {
    setOpenSnackBar(true);
  };

  const handleCloseSnackBar = () => {
    setOpenSnackBar(false);
  };

  const Alert = React.forwardRef<HTMLDivElement, AlertProps>((props, ref) => {
    return <MuiAlert elevation={6} ref={ref} variant="filled" {...props} />;
  });

  return (
    <>
      <Tooltip title={'Create New Assignment'}>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={e => {
            e.stopPropagation();
            setOpen(true);
          }}
        >
          New
        </Button>
      </Tooltip>
      <Dialog open={openDialog} onClose={() => setOpen(false)}>
        <DialogTitle>Create Assignment</DialogTitle>
        <form onSubmit={formik.handleSubmit}>
          <DialogContent>
            <Stack spacing={2}>
              <TextField
                variant="outlined"
                fullWidth
                id="name"
                name="name"
                label="Assignment Name"
                value={formik.values.name}
                onChange={formik.handleChange}
                error={formik.touched.name && Boolean(formik.errors.name)}
                helperText={formik.touched.name && formik.errors.name}
              />

              {/* group field */}
              <InputLabel id="group-description-label">
                Group
                <Tooltip title={groupFeatureDescription}>
                  <HelpOutlineOutlinedIcon
                    fontSize={'small'}
                    sx={{ ml: 1.5, mt: 2 }}
                  />
                </Tooltip>
              </InputLabel>
              <TextField
                variant={'outlined'}
                id={'group'}
                name={'group'}
                label={'Group'}
                value={formik.values.group}
                onChange={formik.handleChange}
              />

              <LocalizationProvider dateAdapter={AdapterDateFns}>
                <FormControlLabel
                  control={
                    <Checkbox
                      value={formik.values.deadline !== null}
                      onChange={async e => {
                        if (e.target.checked) {
                          await formik.setFieldValue('deadline', new Date());
                        } else {
                          await formik.setFieldValue('deadline', null);
                        }
                      }}
                    />
                  }
                  label="Set Deadline"
                />

                <DateTimePicker
                  ampm={false}
                  disabled={formik.values.deadline === null}
                  label="Pick a Date"
                  value={formik.values?.deadline}
                  onChange={date => {
                    formik.setFieldValue('deadline', date);
                    if (new Date(date).getTime() < Date.now()) {
                      handleOpenSnackBar();
                    }
                  }}
                />
                <Snackbar
                  open={openSnackbar}
                  autoHideDuration={6000}
                  onClose={handleCloseSnackBar}
                >
                  <Alert
                    onClose={handleCloseSnackBar}
                    severity="warning"
                    sx={{ width: '100%' }}
                  >
                    You chose date in the past!
                  </Alert>
                </Snackbar>
              </LocalizationProvider>

              <FormControlLabel
                control={
                  <Checkbox
                    value={Boolean(formik.values.max_submissions)}
                    onChange={async e => {
                      if (e.target.checked) {
                        await formik.setFieldValue('max_submissions', 1);
                      } else {
                        await formik.setFieldValue(
                          'max_submissions',
                          undefined
                        );
                      }
                    }}
                  />
                }
                label="Limit Number of Submissions"
              />

              <TextField
                variant="outlined"
                fullWidth
                disabled={!formik.values.max_submissions}
                type={'number'}
                id="max-submissions"
                name="max_submissions"
                placeholder="Submissions"
                value={formik.values.max_submissions}
                onChange={e => {
                  formik.setFieldValue('max_submissions', e.target.value);
                }}
                error={formik.values.max_submissions < 1}
              />

              <InputLabel id="auto-grading-behaviour-label">
                Auto-Grading Behaviour
                <Tooltip title={gradingBehaviourHelp}>
                  <HelpOutlineOutlinedIcon
                    fontSize={'small'}
                    sx={{ ml: 1.5, mt: 1.0 }}
                  />
                </Tooltip>
              </InputLabel>
              <TextField
                select
                id="auto-grading-type-select"
                value={formik.values.autograde_type}
                label="Auto-Grading Behaviour"
                placeholder="Grading"
                onChange={e => {
                  formik.setFieldValue('autograde_type', e.target.value);
                }}
              >
                <MenuItem value={'unassisted'}>No Automatic Grading</MenuItem>
                <MenuItem value={'auto'}>Automatic Grading</MenuItem>
                <MenuItem value={'full_auto'}>Fully Automatic Grading</MenuItem>
              </TextField>
            </Stack>
          </DialogContent>
          <DialogActions>
            <Button
              color="primary"
              variant="outlined"
              onClick={() => {
                setOpen(false);
              }}
            >
              Cancel
            </Button>

            <Button color="primary" variant="contained" type="submit">
              Create
            </Button>
          </DialogActions>
        </form>
      </Dialog>
    </>
  );
};

const InfoModal = () => {
  const [open, setOpen] = React.useState(false);
  const handleOpen = () => {
    setOpen(true);
  };
  const handleClose = () => {
    setOpen(false);
  };
  return (
    <React.Fragment>
      <IconButton color="primary" onClick={handleOpen} sx={{ mr: 2 }}>
        <InfoIcon />
      </IconButton>
      <Modal open={open} onClose={handleClose}>
        <Box
          sx={{
            position: 'absolute' as const,
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            width: '80%',
            bgcolor: 'background.paper',
            boxShadow: 3,
            pt: 2,
            px: 4,
            pb: 3
          }}
        >
          <h2>Selecting Files to Push</h2>
          <Alert severity="info" sx={{ m: 2 }}>
            <AlertTitle>Info</AlertTitle>
            If you have made changes to multiple files in your source directory
            and wish to push only specific files to the remote repository, you
            can toggle the 'Select files to commit' button. This allows you to
            choose the files you want to push. Your students will then be able
            to view only the changes in files you have selected. If you do not
            use this option, all changed files from the source repository will
            be pushed, and students will see all the changes.
          </Alert>
          <Button onClick={handleClose}>Close</Button>
        </Box>
      </Modal>
    </React.Fragment>
  );
};

export interface ICommitDialogProps {
  handleCommit: (msg: string, selectedFiles?: string[]) => void;
  children: React.ReactNode;
  lecture?: Lecture;
  assignment?: Assignment;
}

export const CommitDialog = (props: ICommitDialogProps) => {
  const [open, setOpen] = React.useState(false);
  const [message, setMessage] = React.useState('');
  const selectedDir = 'source';
  const [filesListVisible, setFilesListVisible] = React.useState(false);
  const [selectedFiles, setSelectedFiles] = React.useState<string[]>([]);

  const path = `${lectureBasePath}${props.lecture.code}/${selectedDir}/${props.assignment.id}`;

  const { data: files = [], refetch } = useQuery({
    queryKey: ['commitDialogFiles', path],
    queryFn: () => getFiles(path),
    enabled: false // only fetch when explicitly triggered
  });

  const toggleFilesList = async () => {
    const newVisible = !filesListVisible;
    setFilesListVisible(newVisible);

    if (newVisible) {
      try {
        const fetchedFiles = await refetch();
        const filePaths = fetchedFiles.data.flatMap(file =>
          extractRelativePaths(file, 'source')
        );
        setSelectedFiles(filePaths);
      } catch (error) {
        console.error('Error fetching files:', error);
      }
    }
  };

  const handleFileSelectChange = (filePath: string, isSelected: boolean) => {
    setSelectedFiles(prevSelectedFiles => {
      if (isSelected) {
        if (!prevSelectedFiles.includes(filePath)) {
          return [...prevSelectedFiles, filePath];
        }
      } else {
        return prevSelectedFiles.filter(file => file !== filePath);
      }
      return prevSelectedFiles;
    });
  };

  return (
    <div>
      <Box onClick={() => setOpen(true)}>{props.children}</Box>
      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        fullWidth
        maxWidth="sm"
      >
        <Stack direction="row" justifyContent="space-between">
          <DialogTitle>Commit Files</DialogTitle>
          <InfoModal />
        </Stack>
        <DialogContent>
          <Button onClick={toggleFilesList} sx={{ mb: 2 }}>
            {filesListVisible ? (
              <KeyboardArrowUpIcon />
            ) : (
              <KeyboardArrowRightIcon />
            )}
            Choose files to commit
          </Button>
          {filesListVisible && (
            <FilesList
              files={files}
              lecture={props.lecture}
              assignment={props.assignment}
              checkboxes
              onFileSelectChange={handleFileSelectChange}
              checkStatus
            />
          )}
          <TextField
            sx={{ mt: 2, width: '100%' }}
            label="Commit Message"
            placeholder="Commit Message"
            value={message}
            onChange={event => setMessage(event.target.value)}
            multiline
          />
        </DialogContent>
        <DialogActions>
          <Button
            color="primary"
            variant="outlined"
            onClick={() => {
              setOpen(false);
              setFilesListVisible(false);
            }}
          >
            Cancel
          </Button>

          <Button
            color="primary"
            variant="contained"
            disabled={message === ''}
            onClick={() => {
              props.handleCommit(message, selectedFiles);
              setOpen(false);
              setFilesListVisible(false);
            }}
          >
            Commit
          </Button>
        </DialogActions>
      </Dialog>
    </div>
  );
};

export interface IReleaseDialogProps extends ICommitDialogProps {
  handleRelease: () => void;
}

export const ReleaseDialog = (props: IReleaseDialogProps) => {
  const [commitOpen, setCommitOpen] = React.useState(false);
  const [message, setMessage] = React.useState('');
  const agreeMessage = `Do you want to release "${props.assignment.name}" for all students? Before releasing, all changes are pushed again as the release version.`;

  return (
    <div>
      <Box
        onClick={() => {
          showDialog('Release Assignment', agreeMessage, () => {
            setCommitOpen(true);
          });
        }}
      >
        {props.children}
      </Box>
      <Dialog
        open={commitOpen}
        onClose={() => setCommitOpen(false)}
        fullWidth={true}
        maxWidth={'sm'}
      >
        <DialogTitle>Commit Files</DialogTitle>
        <DialogContent>
          <TextField
            sx={{ mt: 2, width: '100%' }}
            id="outlined-textarea"
            label="Commit Message"
            placeholder="Commit Message"
            value={message}
            onChange={event => setMessage(event.target.value)}
            multiline
          />
        </DialogContent>
        <DialogActions>
          <Button
            color="primary"
            variant="outlined"
            onClick={() => {
              setCommitOpen(false);
            }}
          >
            Cancel
          </Button>

          <GraderLoadingButton
            color="primary"
            variant="contained"
            type="submit"
            disabled={message === ''}
            onClick={async () => {
              await props.handleCommit(message);
              await props.handleRelease();
              setCommitOpen(false);
            }}
          >
            <span>Commit and Release</span>
          </GraderLoadingButton>
        </DialogActions>
      </Dialog>
    </div>
  );
};

interface IExportDialogProps {
  lecture: Lecture;
}

export const ExportGradesForLectureDialog = ({
  lecture
}: IExportDialogProps) => {
  const [openDialog, setOpenDialog] = React.useState(false);
  const [filter, setFilter] = React.useState<'latest' | 'best'>('best');
  const [format, setFormat] = React.useState<'json' | 'csv'>('json');
  const [loading, setLoading] = React.useState(false);

  const handleExport = async () => {
    setLoading(true);
    try {
      await getAllLectureSubmissions(lecture.id, filter, format);
      await openFile(
        `${lectureBasePath}${lecture.code}/${lecture.name}_${filter}_submissions.${format}`
      );
      await openBrowser(`${lectureBasePath}${lecture.code}`);
      if (format === 'csv') {
        enqueueSnackbar('CSV export completed successfully!', {
          variant: 'success'
        });
      } else {
        enqueueSnackbar('JSON export completed successfully!', {
          variant: 'success'
        });
      }
    } catch (error: any) {
      console.error('Error exporting submissions:', error);
      enqueueSnackbar(error.message || 'Failed to export submissions.', {
        variant: 'error'
      });
    } finally {
      setLoading(false);
      setOpenDialog(false);
    }
  };

  return (
    <>
      <Tooltip title="Export grades of all assignments in this lecture in one file.">
        <Button
          variant="contained"
          startIcon={<FileUploadIcon />}
          onClick={() => setOpenDialog(true)}
          sx={{ ml: 2 }}
        >
          Export Grades
        </Button>
      </Tooltip>

      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} fullWidth>
        <DialogTitle>Export Grades</DialogTitle>
        <DialogContent>
          <Typography
            variant="body2"
            color="textSecondary"
            sx={{ fontSize: '0.875rem' }}
          >
            Which grades of student submissions do you wish to export? You can
            either export best or latest grades.
          </Typography>
          <FormControl fullWidth margin="normal">
            <InputLabel>Filter</InputLabel>
            <Select
              value={filter}
              onChange={e => setFilter(e.target.value as 'latest' | 'best')}
              label="Filter"
            >
              <MenuItem value="latest">Latest Submissions</MenuItem>
              <MenuItem value="best">Best Submissions</MenuItem>
            </Select>
          </FormControl>

          <Typography
            variant="body2"
            color="textSecondary"
            sx={{ fontSize: '0.875rem', mt: 2 }}
          >
            Choose the format of the export file. You can either export grades
            in CSV or JSON file.
          </Typography>
          <FormControl fullWidth margin="normal">
            <InputLabel>Format</InputLabel>
            <Select
              value={format}
              onChange={e => setFormat(e.target.value as 'json' | 'csv')}
              label="Format"
            >
              <MenuItem value="json">JSON</MenuItem>
              <MenuItem value="csv">CSV</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>

        <DialogActions>
          <Button
            onClick={() => setOpenDialog(false)}
            color="primary"
            variant="outlined"
          >
            Cancel
          </Button>
          <Button
            onClick={handleExport}
            color="primary"
            variant="contained"
            disabled={loading}
          >
            {loading ? 'Exporting...' : 'Export'}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

interface ISyncSubmissionGrades {
  lecture: Lecture;
  assignment: Assignment;
}

export const SyncSubmissionGradesDialog = ({
  lecture,
  assignment
}: ISyncSubmissionGrades) => {
  const [openDialog, setOpenDialog] = React.useState(false);
  const [filter, setFilter] = React.useState<'latest' | 'best'>('best');
  const [loading, setLoading] = React.useState(false);

  const notifyLtiSyncResult = (
    syncedPlatforms: Array<{
      platform: string;
      syncable_users: number;
      synced_user: number;
    }>
  ) => {
    if (!syncedPlatforms.length) {
      enqueueSnackbar(
        'No connected learning platform was available for grade sync',
        {
          variant: 'info'
        }
      );
      return;
    }

    syncedPlatforms.forEach(platformResult => {
      enqueueSnackbar(
        `${platformResult.platform}: Synced ${platformResult.synced_user}/${platformResult.syncable_users} users`,
        { variant: 'success' }
      );
    });
  };

  const handleSyncSubmission = async () => {
    setLoading(true);
    try {
      const response = await ltiSyncSubmissions(
        lecture.id,
        assignment.id,
        filter
      );
      notifyLtiSyncResult(response.synced_platforms);
    } catch (error: any) {
      enqueueSnackbar(
        'Error while trying to sync submissions: ' + error.message,
        { variant: 'error' }
      );
    } finally {
      setLoading(false);
      setOpenDialog(false);
    }
  };

  return (
    <>
      <Tooltip title="Sync grades of this assignment to Moodle.">
        <Button
          size="small"
          startIcon={<CloudSyncIcon />}
          sx={{ whiteSpace: 'nowrap', minWidth: 'auto' }}
          onClick={() => setOpenDialog(true)}
        >
          LTI Sync Grades
        </Button>
      </Tooltip>

      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} fullWidth>
        <DialogTitle>LTI Sync Grades</DialogTitle>
        <DialogContent>
          <Typography
            variant="body2"
            color="textSecondary"
            sx={{ fontSize: '0.875rem' }}
          >
            Which submission grades do you wish to sync to Moodle? You can
            either sync best or latest grades.
          </Typography>
          <FormControl fullWidth margin="normal">
            <InputLabel>Filter</InputLabel>
            <Select
              value={filter}
              onChange={e => setFilter(e.target.value as 'latest' | 'best')}
              label="Filter"
            >
              <MenuItem value="latest">Latest Submissions</MenuItem>
              <MenuItem value="best">Best Submissions</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>

        <DialogActions>
          <Button
            onClick={() => setOpenDialog(false)}
            color="primary"
            variant="outlined"
          >
            Cancel
          </Button>
          <Button
            onClick={handleSyncSubmission}
            color="primary"
            variant="contained"
            disabled={loading}
          >
            {loading ? 'Syncing...' : 'Sync'}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};
