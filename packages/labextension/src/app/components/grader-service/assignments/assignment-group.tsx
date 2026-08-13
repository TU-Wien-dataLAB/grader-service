import { AssignmentDetail } from '../../../../model/assignmentDetail';
import { ItemTypes } from '../../../shadcn-components/ui/card';
import React, { useRef, useState } from 'react';
import { useDrop } from 'react-dnd';
import { ArrowRightFromLine, ChevronsUpDown } from 'lucide-react';
import { Checkbox } from '../../../shadcn-components/ui/checkbox';
import { IAssignmentChecked } from '../../../pages/instructor-view/lecture';
import { AssignmentCard } from './assignment-card';
import { Button } from '../../../shadcn-components/ui/button';
import { useAssignmentUpdate } from '../../../hooks/assignment/assignment-update-hook';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger
} from '../../../shadcn-components/ui/collapsible';

export interface IAssignmentGroup {
  key: React.Key;
  lectureId: number;
  allAssignments: AssignmentDetail[];
  groupAssignments: IAssignmentChecked[];
  checkedGroupAssignments: IAssignmentChecked[];
  assignmentGroup: string;
  handleGroupChecked: (group: string) => void;
  handleAssignmentChecked: (
    id: number,
    checked: boolean,
    group: string
  ) => void;
  isGroupChecked: boolean | 'indeterminate';
}

export const AssignmentGroup = (props: IAssignmentGroup) => {
  const { handleUpdateAssignment } = useAssignmentUpdate();
  const [isOpenCollapsible, setIsOpenCollapsible] = useState<boolean>(true);

  /* drop logic */
  const ref = useRef<HTMLDivElement>(null);
  const [{ isOver, item }, drop] = useDrop(
    () => ({
      accept: ItemTypes.CARD,
      drop: async (item: { assignmentId: number; group: string }) => {
        await handleDrop(item.assignmentId);
      },
      collect: monitor => ({
        isOver: !!monitor.isOver(),
        item: monitor.getItem()
      })
    }),
    [props]
  );

  drop(ref);

  async function handleDrop(id: number) {
    const assignment = props.allAssignments.filter(
      assignment => assignment.id === id
    )[0];
    if (!assignment) {
      return;
    }
    const oldGroup = assignment.settings.group;
    // check if the assignment had no group and got reassigned to the "ungrouped assignments"
    if (oldGroup === '' && props.assignmentGroup === 'ungrouped assignments') {
      return;
    }
    // check if the group has changed; if not, don't update the assignment
    if (oldGroup === props.assignmentGroup) {
      return;
    }
    let group;
    // update assignment with the new group
    if (props.assignmentGroup === 'ungrouped assignments') {
      group = '';
    } else {
      group = props.assignmentGroup;
    }
    await handleUpdateAssignment(
      assignment,
      { ...assignment, settings: { ...assignment.settings, group: group } },
      props.lectureId
    );
  }

  const determineIfAssignmentBelongsToGroup = (assignmentGroup: string) => {
    return assignmentGroup !== '' && assignmentGroup !== null
      ? assignmentGroup === props.assignmentGroup
      : props.assignmentGroup === 'ungrouped assignments';
  };
  return (
    <div
      className={'flex flex-col gap-2 items-start self-stretch mb-8'}
      ref={ref}
    >
      <Collapsible
        open={isOpenCollapsible}
        onOpenChange={setIsOpenCollapsible}
        className="flex w-full flex-col gap-2"
      >
        <div className="flex justify-between w-full">
          <div className="flex items-center gap-2">
            {props.groupAssignments && (
              <Checkbox
                checked={props.isGroupChecked}
                onCheckedChange={() =>
                  props.handleGroupChecked(props.assignmentGroup)
                }
                disabled={props.groupAssignments.every(
                  a => a.assignment.status !== 'created'
                )}
              ></Checkbox>
            )}
            <h2 className={'text-xl font-bold'}>
              {props.assignmentGroup} ({props.groupAssignments.length})
            </h2>
          </div>
          <CollapsibleTrigger
            render={
              <Button variant="ghost" size="icon" className="size-8">
                <ChevronsUpDown />
                <span className="sr-only">Toggle details</span>
              </Button>
            }
          />
        </div>
        <CollapsibleContent className="flex flex-col gap-2">
          {isOver && (
            <div
              className={`flex p-10 self-stretch ${
                determineIfAssignmentBelongsToGroup(item.group)
                  ? 'bg-[#E0E7EB]'
                  : 'bg-card'
              } py-10 px-14 gap-1.5 border border-dashed border-primary justify-center items-center`}
            >
              <div className={'self-center justify-items-center'}>
                <ArrowRightFromLine className={'text-primary'} />
                <p className={'text-black'}>Drag assignment here</p>
              </div>
            </div>
          )}
          <div
            className={'grid grid-cols-1 @6xl:grid-cols-2 gap-2 self-stretch'}
          >
            {props.checkedGroupAssignments &&
              props.checkedGroupAssignments.map(assignment => (
                <AssignmentCard
                  assignment={assignment.assignment}
                  checked={assignment.checked}
                  handleChange={checked =>
                    props.handleAssignmentChecked(
                      assignment.assignment.id,
                      checked,
                      props.assignmentGroup
                    )
                  }
                  key={assignment.assignment.id}
                />
              ))}
          </div>
        </CollapsibleContent>
      </Collapsible>
    </div>
  );
};
