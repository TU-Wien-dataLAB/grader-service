import {
  AutomaticGradingBadge,
  CompletedAssignmentBadge,
  CreatedAssignmentBadge,
  FullyAutomaticGradingBadge,
  ManualGradingBadge,
  ReleasedAssignmentBadge
} from '../ui/badges';
import React from 'react';
import { AssignmentSettings } from '../../../model/assignmentSettings';
import AutogradeTypeEnum = AssignmentSettings.AutogradeTypeEnum;

export const gradingType = (
  gradingType: AutogradeTypeEnum,
  complete: boolean
) => {
  if (gradingType === AutogradeTypeEnum.FullAuto) {
    return (
      <FullyAutomaticGradingBadge className={complete ? 'opacity-80' : ''} />
    );
  } else if (gradingType === AutogradeTypeEnum.Auto) {
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
