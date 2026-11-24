import {
  AutomaticGradingBadge,
  CompletedAssignmentBadge,
  CreatedAssignmentBadge,
  FullyAutomaticGradingBadge,
  ManualGradingBadge,
  NoFilesBadge,
  OutOfSyncBadge,
  ReleasedAssignmentBadge,
  UnsavedChangesBadge,
  UpdatesAvailableBadge
} from '../../../ui/badges';
import React from 'react';
import { GradingMethod } from '../../../../../model/gradingMethod';
import { RemoteFileStatus } from '../../../../../model/remoteFileStatus';

export const gradingType = (gradingType: GradingMethod, complete: boolean) => {
  if (gradingType === GradingMethod.FullAuto) {
    return (
      <FullyAutomaticGradingBadge className={complete ? 'opacity-80' : ''} />
    );
  } else if (gradingType === GradingMethod.Auto) {
    return <AutomaticGradingBadge className={complete ? 'opacity-80' : ''} />;
  } else {
    return <ManualGradingBadge className={complete ? 'opacity-80' : ''} />;
  }
};

export const assignmentStatus = (status: string) => {
  switch (status) {
    case 'created':
      return <CreatedAssignmentBadge />;
    case 'pushed':
      return <CreatedAssignmentBadge />;
    case 'released':
      return <ReleasedAssignmentBadge />;
    case 'complete':
      return <CompletedAssignmentBadge />;
  }
};

export const assignmentFileStatus = (
  filesLength: number | undefined,
  status: RemoteFileStatus | undefined
) => {
  if (filesLength === 0) {
    return <NoFilesBadge />;
  }
  switch (status) {
    case RemoteFileStatus.UpdateNeeded:
      return <UpdatesAvailableBadge />;
    case RemoteFileStatus.UnsavedChanges:
      return <UnsavedChangesBadge />;
    case RemoteFileStatus.Divergent:
      return <OutOfSyncBadge />;
  }
};
