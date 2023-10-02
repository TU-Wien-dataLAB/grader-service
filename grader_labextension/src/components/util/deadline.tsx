// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import * as React from 'react';
import moment from 'moment';
import {
  Chip,
  Collapse,
  createTheme,
  List, ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText, ListSubheader,
  Typography
} from '@mui/material';
import AccessAlarmRoundedIcon from '@mui/icons-material/AccessAlarmRounded';
import { SxProps, ThemeProvider } from '@mui/system';
import { Theme } from '@mui/material/styles';
import { ExpandLess, ExpandMore } from '@mui/icons-material';
import AlarmIcon from '@mui/icons-material/Alarm';
import AlarmAddIcon from '@mui/icons-material/AlarmAdd';
import { SubmissionPeriod } from '../../model/submissionPeriod';
import { utcToLocalFormat } from '../../services/datetime.service';

export interface IDeadlineProps {
  due_date: string | null;
  compact: boolean;
  component: 'chip' | 'card';
  sx?: SxProps<Theme>;
}

interface ITimeSpec {
  weeks: number;
  days: number;
  hours: number;
  minutes: number;
  seconds: number;
}

interface IUnitMap {
  [name: string]: string;
}

const compactTimeUnits: IUnitMap = {
  w: 'W',
  d: 'd',
  h: 'h',
  m: 'm',
  s: 's'
};

const fullTimeUnits: IUnitMap = {
  w: 'Week',
  d: 'Day',
  h: 'Hour',
  m: 'Minute',
  s: 'Second'
};

const theme = createTheme({
  palette: {
    warning: {
      main: '#ffa726',
      contrastText: '#fff'
    },
    error: {
      main: '#ef5350',
      contrastText: '#fff'
    }
  }
});

const getTimeUnit = (timeUnit: string, value: number, compact: boolean) => {
  if (compact) {
    return `${value}${compactTimeUnits[timeUnit]}`;
  }
  if (value === 1) {
    return `${value} ${fullTimeUnits[timeUnit]}`;
  } else {
    return `${value} ${fullTimeUnits[timeUnit]}s`;
  }
};

export const calculateTimeLeft = (date: Date) => {
  const difference = +date - +new Date();
  const timeLeft: ITimeSpec = {
    weeks: Math.floor(difference / (1000 * 60 * 60 * 24 * 7)),
    days: Math.floor((difference / (1000 * 60 * 60 * 24)) % 7),
    hours: Math.floor((difference / (1000 * 60 * 60)) % 24),
    minutes: Math.floor((difference / 1000 / 60) % 60),
    seconds: Math.floor((difference / 1000) % 60)
  };
  return timeLeft;
};

export function getDisplayDate(date: Date, compact: boolean): string {
  if (date === undefined) {
    return 'No Deadline 😁';
  }
  const time: ITimeSpec = calculateTimeLeft(date);
  if (time.weeks === 0) {
    if (time.days === 0) {
      return `${getTimeUnit('h', time.hours, compact)} ${getTimeUnit(
        'm',
        time.minutes,
        compact
      )} ${getTimeUnit('s', time.seconds, compact)}`;
    } else {
      return `${getTimeUnit('d', time.days, compact)} ${getTimeUnit(
        'h',
        time.hours,
        compact
      )} ${getTimeUnit('m', time.minutes, compact)}`;
    }
  } else if (time.weeks > 0) {
    return `${getTimeUnit('w', time.weeks, compact)} ${getTimeUnit(
      'd',
      time.days,
      compact
    )} ${getTimeUnit('h', time.hours, compact)}`;
  } else {
    return 'Deadline over!';
  }
}

const deadlineColor = (date: Date): 'default' | 'warning' | 'error' => {
  let c: 'default' | 'warning' | 'error' = 'default';
  const time: ITimeSpec = calculateTimeLeft(date);
  if (date !== undefined) {
    if (time.weeks === 0 && time.days === 0) {
      c = 'warning';
      if (time.hours === 0) {
        c = 'error';
      }
    }
    if (+date - +new Date() < 0) {
      c = 'error';
    }
  }
  return c;
};

export const DeadlineComponent = (props: IDeadlineProps) => {
  const [date, setDate] = React.useState(
    props.due_date !== null
      ? moment.utc(props.due_date).local().toDate()
      : undefined
  );
  const [displayDate, setDisplayDate] = React.useState(
    getDisplayDate(date, props.compact)
  );
  const [interval, setNewInterval] = React.useState(null);
  const [color, setColor] = React.useState(
    'default' as 'default' | 'warning' | 'error'
  );

  React.useEffect(() => {
    const d =
      props.due_date !== null
        ? moment.utc(props.due_date).local().toDate()
        : undefined;
    setDate(d);
    setDisplayDate(getDisplayDate(d, props.compact));
    updateTimeoutInterval(d);
    const c = deadlineColor(d);
    setColor(c);
  }, [props]);

  const updateTimeoutInterval = (date: Date) => {
    if (interval) {
      clearInterval(interval);
    }
    const time: ITimeSpec = calculateTimeLeft(date);
    const timeout = time.weeks === 0 && time.days === 0 ? 1000 : 10000;
    const newInterval = setInterval(() => {
      setDisplayDate(getDisplayDate(date, props.compact));
    }, timeout);
    setNewInterval(newInterval);
  };

  return (
    <ThemeProvider theme={theme}>
      <Chip
        sx={props.sx}
        size='small'
        icon={<AccessAlarmRoundedIcon />}
        label={displayDate}
        color={color}
      />
    </ThemeProvider>

  );
};

interface IDeadlineDetailProps {
  due_date: string | null;
  late_submissions: SubmissionPeriod[];
}

export function DeadlineDetail(props: IDeadlineDetailProps) {
  if (props.due_date === null) {
    return null;
  }
  const [open, setOpen] = React.useState(true);

  const [date, setDate] = React.useState(
    props.due_date !== null
      ? moment.utc(props.due_date).local().toDate()
      : undefined
  );
  const [displayDuration, setDisplayDuration] = React.useState(
    getDisplayDate(date, false)
  );
  const [interval, setNewInterval] = React.useState(null);
  const [color, setColor] = React.useState(
    'default' as 'default' | 'warning' | 'error'
  );

  const updateTimeoutInterval = (date: Date) => {
    if (interval) {
      clearInterval(interval);
    }
    const time: ITimeSpec = calculateTimeLeft(date);
    const timeout = time.weeks === 0 && time.days === 0 ? 1000 : 10000;
    const newInterval = setInterval(() => {
      setDisplayDuration(getDisplayDate(date, false));
    }, timeout);
    setNewInterval(newInterval);
  };

  React.useEffect(() => {
    const d =
      props.due_date !== null
        ? moment.utc(props.due_date).local().toDate()
        : undefined;
    setDisplayDuration(getDisplayDate(d, false));
    updateTimeoutInterval(d);
    const c = deadlineColor(d);
    setColor(c);
  }, [props]);

  const handleClick = () => {
    setOpen(!open);
  };

  if (props.late_submissions.length === 0) {
    return <List component='nav' subheader={
      <ListSubheader
        sx={{ lineHeight: 1 }}
        component='div'
        id='late-submission-list-subheader'
      >
        Deadline
      </ListSubheader>
    }>
      <ListItem onClick={handleClick}>
        <ListItemIcon>
          <AlarmIcon color={color === 'default' ? 'action' : color} />
        </ListItemIcon>
        <ListItemText primary={utcToLocalFormat(props.due_date)} />
        <ListItemText primary={<Typography color={'text.secondary'}>{displayDuration}</Typography>} />
      </ListItem>
    </List>;
  } else {
    return (
      <List component='nav' subheader={
        <ListSubheader
          sx={{ lineHeight: 1 }}
          component='div'
          id='late-submission-list-subheader'
        >
          Deadline
        </ListSubheader>
      }>
        <ListItemButton onClick={handleClick}>
          <ListItemIcon>
            <AlarmIcon color={color === 'default' ? 'action' : color} />
          </ListItemIcon>
          <ListItemText primary={utcToLocalFormat(props.due_date)} />
          <ListItemText primary={<Typography color={'text.secondary'}>{displayDuration}</Typography>} />
          <Typography
            color={'text.secondary'}>{`${props.late_submissions.length} Extension${props.late_submissions.length !== 1 ? 's' : ''}`}</Typography>
          {open ? <ExpandLess /> : <ExpandMore />}
        </ListItemButton>
        <Collapse in={open} timeout='auto'>
          <List
            dense
            component='div'
            disablePadding
            subheader={
              <ListSubheader
                sx={{ lineHeight: 1 }}
                component='div'
                id='late-submission-list-subheader'
              >
                Extensions
              </ListSubheader>
            }
          >
            {props.late_submissions.map(l => {
              const p = moment.duration(l.period);
              return <ListItem sx={{ pl: 4 }}>
                <ListItemIcon>
                  <AlarmAddIcon />
                </ListItemIcon>
                <ListItemText primary={`${p.days()} Days ${p.hours()} Hours`} />
                <ListItemText primary={`Penalty: ${(1 - l.scaling) * 100}%`} />
              </ListItem>;
            })}
          </List>
        </Collapse>
      </List>
    );
  }
}

