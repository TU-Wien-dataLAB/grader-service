import { Badge } from '../../shadcn-components/ui/badge';
import React from 'react';
import { AutoStatus } from '../../../model/autoStatus';

const commonStyle = 'text-foreground';

// Add type and properties to add a new badge

export type BadgeType =
  | AutoStatus
  | 'manually_graded'
  | 'edited'
  | 'completed'
  | 'released'
  | 'not_released'
  | 'manual_grading'
  | 'automatic_grading'
  | 'fully_automatic_grading';

export const gradingBadge: Record<
  BadgeType,
  { label: string; className: string }
> = {
  pending: {
    label: 'Pending',
    className: 'bg-[#DBDBDB] border-[#B8B8B8]'
  },
  grading_failed: {
    label: 'Grading failed',
    className: 'bg-[#FF9999] border-[#CC7373]'
  },
  automatically_graded: {
    label: 'Automatically graded',
    className: 'bg-[#FFC89E] border-[#FF9D52]'
  },
  not_graded: {
    label: 'Not graded',
    className: 'bg-[#FF9999] border-[#CC7373]'
  },
  manually_graded: {
    label: 'Manually graded',
    className: 'bg-[#AEDCE5] border-[#8CB0B8]'
  },
  edited: {
    label: 'Edited',
    className: 'bg-[#FFEB99] border-[#F5C918]'
  },
  completed: {
    label: 'Completed',
    className: 'bg-primary border-primary-hover opacity-80'
  },
  released: {
    label: 'Released',
    className: 'bg-[#CED662] border-[#ACB252]'
  },
  not_released: {
    label: 'Not released',
    className: 'bg-[#FF9090] border-[#CC7373]'
  },
  manual_grading: {
    label: 'Manual grading',
    className: 'bg-[#AEDCE5] border-[#8CB0B8]'
  },
  automatic_grading: {
    label: 'Automatic grading',
    className: 'bg-[#FFC89E] border-[#FF9D52]'
  },
  fully_automatic_grading: {
    label: 'Fully automatic grading',
    className: 'bg-[#DAAFFA] border-[#9C7DB2]'
  }
};

interface ICustomBadgeProps {
  type: BadgeType;
  className?: string;
}

export const CustomBadge = ({ type, className = '' }: ICustomBadgeProps) => {
  const { label, className: badgeClassName } = gradingBadge[type];

  return (
    <Badge className={`${commonStyle} ${badgeClassName} ${className}`}>
      {label}
    </Badge>
  );
};
