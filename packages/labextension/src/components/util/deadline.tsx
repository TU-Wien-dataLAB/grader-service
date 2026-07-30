// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import * as React from 'react';
import moment from 'moment';
import { Clock } from 'lucide-react';
import { Badge } from '../../app/shadcn-components/ui/badge';

export interface IDeadlineProps {
  deadline: string | null;
  compact: boolean;
  component: 'chip' | 'card';
  className?: string;
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

const colorClass = (color: 'default' | 'warning' | 'error') => {
  if (color === 'error') {
    return 'bg-destructive text-white';
  }
  if (color === 'warning') {
    return 'bg-yellow-500 text-white';
  }
  return 'bg-secondary text-foreground';
};

export const DeadlineComponent = (props: IDeadlineProps) => {
  const [date, setDate] = React.useState(
    props.deadline !== null
      ? moment.utc(props.deadline).local().toDate()
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
      props.deadline !== null
        ? moment.utc(props.deadline).local().toDate()
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
    <Badge className={colorClass(color)}>
      <Clock className="size-3" />
      {displayDate}
    </Badge>
  );
};
