import moment from 'moment/moment';
import React from 'react';

export const pluralize = (props: { text: string; data: any }) => {
  return props.data.length === 1 || props.data === 1
    ? props.text
    : `${props.text}s`;
};

export const calculateDaysDifference = (props: {
  startDate: Date;
  endDate: Date;
}) => {
  const diffMs = Math.abs(props.endDate.getTime() - props.startDate.getTime());

  const daysDiff = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  const hoursDiff = Math.floor(
    (diffMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60)
  );
  const minutesDiff = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
  return { daysDiff, hoursDiff, minutesDiff };
};

export const buildPeriod = (days: number, hours: number) => {
  return moment.duration({ days, hours }).toISOString();
};

export const getDate = (date: Date) => moment(date).format('DD.MM.YYYY');

export function highlightText(text: string, query: string): React.ReactNode {
  if (!query.trim()) {
    return text;
  }

  const escapedQuery = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const regex = new RegExp(`(${escapedQuery})`, 'gi');
  const parts = text.split(regex);

  return parts.map((part, index) =>
    regex.test(part) ? (
      <mark key={index} className="bg-[#FFEDD6] text-inherit">
        {part}
      </mark>
    ) : (
      part
    )
  );
}
