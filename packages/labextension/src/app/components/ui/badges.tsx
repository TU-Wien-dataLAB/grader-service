import { Badge } from '../../shadcn-components/ui/badge';
import React from 'react';

const commonStyle = 'text-foreground';

export const FullyAutomaticGradingBadge = ({
  className = ''
}: {
  className?: string;
}) => {
  return (
    <Badge
      className={`${className}${commonStyle} bg-[#DAAFFA] border-[#9C7DB2]`}
    >
      Fully automatic grading
    </Badge>
  );
};

export const AutomaticGradingBadge = ({
  className = ''
}: {
  className?: string;
}) => {
  return (
    <Badge
      className={`${className} ${commonStyle} bg-[#FFC89E] border-[#FF9D52]`}
    >
      Automatic grading
    </Badge>
  );
};

export const ManualGradingBadge = ({
  className = ''
}: {
  className?: string;
}) => {
  return (
    <Badge
      className={`${className} ${commonStyle} bg-[#AEDCE5] border-[#8CB0B8]`}
    >
      Manual grading
    </Badge>
  );
};

export const CreatedAssignmentBadge = ({
  className = ''
}: {
  className?: string;
}) => {
  return (
    <Badge
      className={`${className} ${commonStyle} bg-[#FF9090] border-[#CC7373]`}
    >
      Not released
    </Badge>
  );
};

export const ReleasedAssignmentBadge = ({
  className = ''
}: {
  className?: string;
}) => {
  return (
    <Badge
      className={`${className} ${commonStyle} bg-[#CED662] border-[#ACB252]`}
    >
      Released
    </Badge>
  );
};

export const CompletedAssignmentBadge = ({
  className = ''
}: {
  className?: string;
}) => {
  return (
    <Badge
      className={`${className} ${commonStyle} bg-primary border-primary-hover opacity-80`}
    >
      Completed
    </Badge>
  );
};

export const NoFilesBadge = ({ className = '' }: { className?: string }) => {
  return (
    <Badge
      className={`${className} ${commonStyle} bg-gray-400 border-gray-500`}
    >
      No files
    </Badge>
  );
};

export const NoBackupBadge = ({ className = '' }: { className?: string }) => {
  return (
    <Badge
      className={`${className} ${commonStyle} bg-gray-400 border-gray-500`}
    >
      No backup
    </Badge>
  );
};

export const UpToDateBadge = ({ className = '' }: { className?: string }) => {
  return (
    <Badge
      className={`${className} ${commonStyle} bg-lime-600 border-lime-700`}
    >
      Up to date
    </Badge>
  );
};

export const UpdatesAvailableBadge = ({
  className = ''
}: {
  className?: string;
}) => {
  return (
    <Badge
      className={`${className} ${commonStyle} bg-blue-400 border-blue-500`}
    >
      Updates available
    </Badge>
  );
};

export const OutOfSyncBadge = ({ className = '' }: { className?: string }) => {
  return (
    <Badge className={`${className} ${commonStyle} bg-red-600 border-red-700`}>
      Out of sync
    </Badge>
  );
};

export const UnsavedChangesBadge = ({
  className = ''
}: {
  className?: string;
}) => {
  return (
    <Badge
      className={`${className} ${commonStyle} bg-yellow-400 border-yellow-500`}
    >
      Unsaved changes
    </Badge>
  );
};
