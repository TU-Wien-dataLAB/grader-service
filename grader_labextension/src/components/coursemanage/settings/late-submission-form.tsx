import { SubmissionPeriod } from '../../../model/submissionPeriod';
import React from 'react';
import { Box, Button, IconButton, InputLabel, Stack, TextField, Tooltip } from '@mui/material';
import ClearIcon from '@mui/icons-material/Clear';
import moment from 'moment';

const duration_from_values = (days: number, hours: number): string => {
  return `P${days}DT${hours}H`;
};

interface ILateSubmissionInfo {
  days: number;
  hours: number;
  scaling: number;
}

const values_from_duration = (period: string, scaling: number): ILateSubmissionInfo => {
  const d = moment.duration(period);
  return { days: d.days(), hours: d.hours(), scaling };
};

export const getLateSubmissionInfo = (lateSubmissions: SubmissionPeriod[]): ILateSubmissionInfo[] => {
  lateSubmissions = lateSubmissions || [];
  return lateSubmissions.map(l => values_from_duration(l.period, l.scaling));
};

interface ILateSubmissionFormProps {
  formik: any;
}

export const LateSubmissionForm = (props: ILateSubmissionFormProps) => {
  const formik = props.formik;
  // let lateSubmissions: ILateSubmissionInfo[] = props.formik.values.lateSubmissions;

  const updateLateSubmissions = (lateSubmissions: ILateSubmissionInfo[]) => {
    console.log(lateSubmissions);
    formik.setFieldValue('lateSubmissions', lateSubmissions);
  };

  const updateLateSubmissionValue = (i: number, key: keyof ILateSubmissionInfo, value: number) => {
    formik.values.lateSubmissions[i][key] = value;
    updateLateSubmissions(formik.values.lateSubmissions);
  };

  const addLateSubmission = () => {
    formik.values.lateSubmissions.push({ days: 0, hours: 0, scaling: 0 });
    updateLateSubmissions(formik.values.lateSubmissions);
  };

  const removeLateSubmission = (i: number) => {
    formik.values.lateSubmissions.splice(i, 1);
    updateLateSubmissions(formik.values.lateSubmissions);
  };

  return (
    <Stack direction={'column'} spacing={2}>
      <InputLabel>
        Late Submissions
      </InputLabel>
      {formik.values.lateSubmissions.map((l, i) => <Stack direction={'row'} spacing={2}>
        <TextField id={`days_${i}`} label={'Days'} value={l.days}
                   onChange={e => updateLateSubmissionValue(i, 'days', +e.target.value)} />
        <TextField id={`hours${i}`} label={'Hours'} value={l.hours}
                   onChange={e => updateLateSubmissionValue(i, 'hours', +e.target.value)} />
        <TextField id={`scaling${i}`} label={'Scaling'} value={l.scaling}
                   onChange={e => updateLateSubmissionValue(i, 'scaling', +e.target.value)} />
        <IconButton onClick={() => removeLateSubmission(i)}><ClearIcon /></IconButton>
      </Stack>)}
      <Button onClick={() => addLateSubmission()}>New</Button>
    </Stack>
  );
};