// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import * as React from 'react';
import moment from 'moment';
import { CardContent, Chip, Typography } from '@mui/material';
import AccessAlarmRoundedIcon from '@mui/icons-material/AccessAlarmRounded';
import { SxProps } from '@mui/system';
import { Theme } from '@mui/material/styles';
import { red, orange, grey } from '@mui/material/colors';

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

const calculateTimeLeft = (date: Date) => {
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

function getDisplayDate(date: Date, compact: boolean): string {
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

function getCardColor(c: 'default' | 'warning' | 'error') {
  if (c === 'default') {
    return grey[300];
  } else if (c === 'warning') {
    return orange[500];
  } else {
    return red[500];
  }
}

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
    let c: 'default' | 'warning' | 'error' = 'default';
    const time: ITimeSpec = calculateTimeLeft(d);
    if (d !== undefined) {
      if (time.weeks === 0 && time.days === 0) {
        c = 'warning';
        if (time.hours === 0) {
          c = 'error';
        }
      }
      if (+d - +new Date() < 0) {
        c = 'error';
      }
    }
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

  return props.component === 'chip' ? (
    <Chip
      sx={props.sx}
      size="small"
      icon={<AccessAlarmRoundedIcon />}
      label={displayDate}
      color={color}
    />
  ) : (
    <CardContent
      sx={{ backgroundColor: getCardColor(color), p: 1, width: '100%' }}
    >
      <Typography variant="overline" align="left" sx={{ fontSize: 9, ml: 1 }}>
        Deadline
      </Typography>
      <Typography align="center" sx={{ fontSize: 12, m: 0, mt: -1 }}>
        {displayDate}
      </Typography>
    </CardContent>
  );
};
