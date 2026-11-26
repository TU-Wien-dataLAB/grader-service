import {
  AutomaticGradingBadge,
  CompletedAssignmentBadge,
  CreatedAssignmentBadge,
  FullyAutomaticGradingBadge,
  ManualGradingBadge,
  ReleasedAssignmentBadge
} from '../ui/badges';
import React from 'react';
import { GradingMethod } from '../../../model/gradingMethod';

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
