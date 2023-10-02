import { SubmissionPeriod } from '../../../model/submissionPeriod';
import React from 'react';
import { Box, Button, IconButton, InputLabel, Stack, TextField, Tooltip } from '@mui/material';
import ClearIcon from '@mui/icons-material/Clear';
import moment from 'moment';
import { AssignmentSettings } from '../../../model/assignmentSettings';

const duration_from_values = (days: number, hours: number): string => {
  return `P${days}DT${hours}H`;
};

export interface ILateSubmissionInfo {
  days: number;
  hours: number;
  scaling: number;
}

const values_from_duration = (period: string, scaling: number): ILateSubmissionInfo => {
  const d = moment.duration(period);
  return { days: d.days(), hours: d.hours(), scaling: scaling || 0.0 };
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

  const updateSettings = (settings: AssignmentSettings) => {
    formik.setFieldValue('settings', settings);
  };

  const updateLateSubmissionValue = (i: number, key: keyof ILateSubmissionInfo, value: number) => {
    const period = formik.values.settings.late_submission[i];
    const late_sub_info = values_from_duration(period.period, period.scaling);
    late_sub_info[key] = value;
    formik.values.settings.late_submission[i] = {
      period: duration_from_values(late_sub_info.days, late_sub_info.hours),
      scaling: late_sub_info.scaling
    };
    updateSettings(formik.values.settings);
  };

  const addLateSubmission = () => {
    let scaling = 0.5;
    let days = 1;
    let hours = 0;
    const numPeriods = formik.values?.settings?.late_submission?.length;
    if (numPeriods > 0) {
      const prevPeriod = formik.values?.settings?.late_submission[numPeriods - 1];
      const prevInfo = values_from_duration(prevPeriod.period, prevPeriod.scaling);
      scaling = prevInfo.scaling / 2;
      days = prevInfo.days + 1;
      hours = prevInfo.hours;
    }
    formik.values.settings.late_submission.push({ period: duration_from_values(days, hours), scaling: scaling });
    updateSettings(formik.values.settings);
  };

  const removeLateSubmission = (i: number) => {
    formik.values.settings.late_submission.splice(i, 1);
    updateSettings(formik.values.settings);
  };

  return (
    <>
      {formik.values.settings.late_submission.map((l: SubmissionPeriod, i: number) => {
        const late_sub_info = values_from_duration(l.period, l.scaling);
        return <Stack direction={'row'} spacing={2}>
          <TextField id={`days_${i}`} label={'Days'} value={late_sub_info.days} type={'number'}
                     error={i in (formik.errors?.late_submission?.days || {})}
                     helperText={i in (formik.errors?.late_submission?.days || {}) && formik.errors.late_submission?.days[i]}
                     onChange={e => updateLateSubmissionValue(i, 'days', +e.target.value)} />
          <TextField id={`hours${i}`} label={'Hours'} value={late_sub_info.hours} type={'number'}
                     error={i in (formik.errors?.late_submission?.hours || {})}
                     helperText={i in (formik.errors?.late_submission?.hours || {}) && formik.errors.late_submission?.hours[i]}
                     onChange={e => updateLateSubmissionValue(i, 'hours', +e.target.value)} />
          <TextField id={`scaling${i}`} label={'Scaling'} value={late_sub_info.scaling} type={'number'}
                     inputProps={{ maxLength: 4, step: '0.01', min: 0.0, max: 1.0 }}
                     error={i in (formik.errors?.late_submission?.scaling || {})}
                     helperText={i in (formik.errors?.late_submission?.scaling || {}) && formik.errors.late_submission?.scaling[i]}
                     onChange={e => updateLateSubmissionValue(i, 'scaling', +e.target.value)} />
          <IconButton onClick={() => removeLateSubmission(i)}><ClearIcon /></IconButton>
        </Stack>;
      })}
      <Button variant={'outlined'} onClick={() => addLateSubmission()}>Add Late Submission Period</Button>
    </>);
};