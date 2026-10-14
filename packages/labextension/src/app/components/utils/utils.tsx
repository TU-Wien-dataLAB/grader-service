import moment from 'moment/moment';
import React from 'react';
import { FileRow } from '../grader-service/notebooks-and-files/files-table';

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

const UNITS = ['B', 'kB', 'MB', 'GB', 'TB'];
// Returns the size in bytes; directories are the sum of their children.
function getFileSizeInBytes(file: FileRow): number {
  if (file.type === 'directory') {
    return (file.subRows ?? []).reduce(
      (total, child) => total + getFileSizeInBytes(child),
      0
    );
  }
  return file.size ?? 0;
}

function formatBytes(bytes: number): string {
  if (!bytes || bytes <= 0) {
    return '0 B';
  }
  const i = Math.min(
    Math.floor(Math.log(bytes) / Math.log(1024)),
    UNITS.length - 1
  );
  return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${UNITS[i]}`;
}

// Drop-in replacement for your original function.
export function determineFileSize(file: FileRow): string {
  return formatBytes(getFileSizeInBytes(file));
}
