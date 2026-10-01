import React from 'react';
import {
  CompletedAssignmentBadge,
  CreatedAssignmentBadge,
  ReleasedAssignmentBadge
} from '../../../ui/badges';
import { Badge } from '../../../../shadcn-components/ui/badge';
import { Checkbox } from '../../../../shadcn-components/ui/checkbox';
import { CornerDownRight } from 'lucide-react';
import { IAssignmentChecked } from '../../../../pages/instructor-view/lecture';
import { Assignment } from '../../../../../model/assignment';
import { Label } from '../../../../shadcn-components/ui/label';

interface IAssignmentGroupedCheckboxList {
  assignments: IAssignmentChecked[];
  groupName: string;
  checkGroupSymbol: (group: string) => boolean | 'indeterminate';
  handleGroupChecked: (group: string) => void;
  handleAssignmentChecked: (
    id: number,
    checked: boolean,
    group: string
  ) => void;
}

const AssignmentGroupedCheckboxList = (
  props: IAssignmentGroupedCheckboxList
) => {
  const {
    assignments,
    groupName,
    checkGroupSymbol,
    handleAssignmentChecked,
    handleGroupChecked
  } = props;

  const assignmentStatus = (assignment: Assignment) => {
    const status = assignment.status;
    switch (status) {
      case 'created':
        return <CreatedAssignmentBadge />;
      case 'pushed':
        return <Badge>Pushed</Badge>;
      case 'released':
        return <ReleasedAssignmentBadge />;
      case 'complete':
        return <CompletedAssignmentBadge />;
    }
  };

  return (
    <div className={'flex flex-col items-start w-full max-h-80'}>
      <div className={'inline-flex min-h-8 items-start rounded-xs gap-2'}>
        <Checkbox
          checked={checkGroupSymbol(groupName)}
          onCheckedChange={() => handleGroupChecked(groupName)}
        />
        <Label>{groupName}</Label>
      </div>
      <ul className={'w-full overflow-y-auto'}>
        {assignments.map(a => (
          <li className={'flex min-h-8 items-center gap-2'}>
            <CornerDownRight className={'size-4 text-border shrink-0'} />
            <Checkbox
              checked={a.checked}
              disabled={a.assignment.status !== 'created'}
              onCheckedChange={() =>
                handleAssignmentChecked(a.assignment.id, !a.checked, groupName)
              }
            />
            <p
              className={`${
                a.assignment.status === 'created'
                  ? 'text-secondary-background'
                  : 'text-border'
              } truncate`}
            >
              {a.assignment.name}
            </p>
            <div className={'ml-auto'}>{assignmentStatus(a.assignment)}</div>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default AssignmentGroupedCheckboxList;
