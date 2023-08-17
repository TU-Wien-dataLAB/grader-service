import { Assignment } from '../../../model/assignment';
import { Submission } from '../../../model/submission';
import * as React from 'react';
import { ErrorMessage, useFormik } from 'formik';
import {
  Box,
  Button,
  Checkbox,
  FormControlLabel,
  InputLabel,
  MenuItem,
  Stack,
  TextField,
  Tooltip
} from '@mui/material';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { DateTimePicker } from '@mui/x-date-pickers/DateTimePicker';
import HelpOutlineOutlinedIcon from '@mui/icons-material/HelpOutlineOutlined';
import {
  deleteAssignment,
  updateAssignment
} from '../../../services/assignments.service';
import { enqueueSnackbar } from 'notistack';
import { Lecture } from '../../../model/lecture';
import * as yup from 'yup';
import { SectionTitle } from '../../util/section-title';
import { useRouteLoaderData } from 'react-router-dom';

const gradingBehaviourHelp = `Specifies the behaviour when a students submits an assignment.\n
No Automatic Grading: No action is taken on submit.\n
Automatic Grading: The assignment is being autograded as soon as the students makes a submission.\n
Fully Automatic Grading: The assignment is autograded and feedback is generated as soon as the student makes a submission. 
(requires all scores to be based on autograde results)`;

const validationSchema = yup.object({
  name: yup
    .string()
    .min(4, 'Name should be 4-50 character length')
    .max(50, 'Name should be 4-50 character length')
    .required('Name is required'),
  due_date: yup
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


//export interface ISettingsProps {
//  root: HTMLElement;
//}

export const SettingsComponent = () => {

  const { lecture, assignments } = useRouteLoaderData('lecture') as {
      lecture: Lecture,
      assignments: Assignment[],
  };

  const { assignment, allSubmissions, latestSubmissions } = useRouteLoaderData('assignment') as {
      assignment: Assignment,
      allSubmissions: Submission[],
      latestSubmissions: Submission[]
  };

  const [checked, setChecked] = React.useState(
    assignment.due_date !== null
  );
  const [checkedLimit, setCheckedLimit] = React.useState(
    Boolean(assignment.max_submissions)
  );
  
  

  const formik = useFormik({
    initialValues: {
      name: assignment.name,
      due_date:
        assignment.due_date !== null
          ? new Date(assignment.due_date)
          : null,
      type: assignment.type,
      automatic_grading: assignment.automatic_grading,
      max_submissions: assignment.max_submissions || null,
      allow_files: assignment.allow_files || false
    },
    validationSchema: validationSchema,
    onSubmit: values => {
      if (values.max_submissions !== null) {
        values.max_submissions = +values.max_submissions;
      }
      const updatedAssignment: Assignment = Object.assign(
        assignment,
        values
      );
      updateAssignment(lecture.id, updatedAssignment).then(
        response => {
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
    }
  });

  return (
    <Box ml={'50px'} mr={'50px'}>
      <SectionTitle title="Settings" />
      <form onSubmit={formik.handleSubmit}>
        <Stack spacing={2} sx={{ ml: 2, mr: 2 }}>
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

          <LocalizationProvider dateAdapter={AdapterDateFns}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={checked}
                  onChange={async e => {
                    setChecked(e.target.checked);
                    if (!e.target.checked) {
                      await formik.setFieldValue('due_date', null);
                    } else {
                      await formik.setFieldValue('due_date', new Date());
                    }
                  }}
                />
              }
              label="Set Deadline"
            />
            <DateTimePicker
              ampm={false}
              disabled={!checked}
              label="DateTimePicker"
              disablePast
              value={formik.values.due_date}
              onChange={(date: Date) => {
                formik.setFieldValue('due_date', date);
              }}
            />
          </LocalizationProvider>

          <FormControlLabel
            control={
              <Checkbox
                checked={checkedLimit}
                onChange={async e => {
                  setCheckedLimit(e.target.checked);
                  if (!e.target.checked) {
                    await formik.setFieldValue('max_submissions', null);
                  } else {
                    await formik.setFieldValue('max_submissions', 1);
                  }
                }}
              />
            }
            label="Limit Number of Submissions"
          />

          <TextField
            variant="outlined"
            fullWidth
            disabled={!checkedLimit}
            type={'number'}
            id="max-submissions"
            name="max_submissions"
            placeholder="Submissions"
            value={formik.values.max_submissions || null}
            InputProps={{ inputProps: { min: 1 } }}
            onChange={e => {
              formik.setFieldValue('max_submissions', +e.target.value);
            }}
            helperText={
              formik.touched.max_submissions && formik.errors.max_submissions
            }
            error={
              Boolean(formik.values.max_submissions) &&
              formik.values.max_submissions < 1
            }
          />

          <InputLabel id="demo-simple-select-label-auto">
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
            id="assignment-type-select"
            value={formik.values.automatic_grading}
            label="Auto-Grading Behaviour"
            placeholder="Grading"
            onChange={e => {
              formik.setFieldValue('automatic_grading', e.target.value);
            }}
          >
            <MenuItem value={'auto'}>Automatic Grading</MenuItem>
            <MenuItem value={'full_auto'}>Fully Automatic Grading</MenuItem>
            <MenuItem value={'unassisted'}>No Automatic Grading</MenuItem>
          </TextField>

          <FormControlLabel
            control={
              <Checkbox
                checked={formik.values.allow_files}
                onChange={async e => {
                  console.log(e.target.checked);
                  await formik.setFieldValue('allow_files', e.target.checked);
                }}
              />
            }
            label="Allow file upload by students"
          />

          {/* Not included in release 0.1
              <InputLabel id="demo-simple-select-label">Type</InputLabel>
              <Select
                labelId="assignment-type-select-label"
                id="assignment-type-select"
                value={formik.values.type}
                label="Type"
                disabled={
                  assignment.status === 'complete' ||
                  assignment.status === 'released'
                }
                onChange={e => {
                  formik.setFieldValue('type', e.target.value);
                }}
              >
                <MenuItem value={'user'}>User</MenuItem>
                <MenuItem value={'group'}>Group</MenuItem>
              </Select>*/}
        </Stack>
      <Button color="primary" variant="contained" type="submit">
        Save changes
      </Button>
      </form>
    </Box>
  );
};
