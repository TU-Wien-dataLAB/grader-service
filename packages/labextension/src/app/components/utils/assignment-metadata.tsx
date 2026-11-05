import { CustomBadge } from '../ui/badges';
import React from 'react';
import { AssignmentSettings } from '../../../model/assignmentSettings';
import AutogradeTypeEnum = AssignmentSettings.AutogradeTypeEnum;

export const gradingType = (
  gradingType: AutogradeTypeEnum,
  complete: boolean
) => {
  if (gradingType === AutogradeTypeEnum.FullAuto) {
    return (
      <CustomBadge
        type="fully_automatic_grading"
        className={complete ? 'opacity-80' : ''}
      />
    );
  } else if (gradingType === AutogradeTypeEnum.Auto) {
    return (
      <CustomBadge
        type="automatic_grading"
        className={complete ? 'opacity-80' : ''}
      />
    );
  } else {
    return (
      <CustomBadge
        type="manual_grading"
        className={complete ? 'opacity-80' : ''}
      />
    );
  }
};

export const assignmentStatus = (status: string) => {
  switch (status) {
    case 'created':
      return <CustomBadge type="not_released" />;
    case 'pushed':
      return <CustomBadge type="not_released" />;
    case 'released':
      return <CustomBadge type="released" />;
    case 'complete':
      return <CustomBadge type="completed" />;
  }
};
