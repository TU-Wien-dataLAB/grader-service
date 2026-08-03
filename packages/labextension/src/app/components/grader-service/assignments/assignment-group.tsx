import { AssignmentDetail } from '../../../../model/assignmentDetail';
import { ItemTypes } from '../../../shadcn-components/ui/card';
import React, { useEffect, useRef, useState } from 'react';
import { useDrop } from 'react-dnd';
import { updateAssignment } from '../../../../services/assignments.service';
import { ArrowRightFromLine } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import { Checkbox } from '../../../shadcn-components/ui/checkbox';
import { IAssignmentChecked } from '../../../pages/instructor-view/lecture';
import { AssignmentCard } from './assignment-card';
import { Button } from '../../../shadcn-components/ui/button';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger
} from '../../../shadcn-components/ui/tooltip';
import { ReleaseDialog } from './release-dialog';

export interface IAssignmentGroup {
  key: React.Key;
  lectureId: number;
  allAssignments: AssignmentDetail[];
  groupAssignments: IAssignmentChecked[];
  assignmentGroup: string;
}

export const AssignmentGroup = (props: IAssignmentGroup) => {
  const queryClient = useQueryClient();
  const [openReleaseDialog, setOpenReleaseDialog] = useState(false);
  const [checkedAssignments, setCheckedAssignments] =
    useState<IAssignmentChecked[]>(null);
  // NOTE: maybe not the best way to do this, but is a workaround for now
  useEffect(() => {
    setCheckedAssignments(props.groupAssignments);
  }, [props.groupAssignments]);

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
    // update assignment with the new group
    if (props.assignmentGroup === 'ungrouped assignments') {
      assignment.settings.group = '';
    } else {
      assignment.settings.group = props.assignmentGroup;
    }
    // TODO: use mutation function
    await updateAssignment(props.lectureId, assignment, false);
    await queryClient.invalidateQueries({
      queryKey: ['assignments', props.lectureId]
    });
  }

  /* checkbox logic */
  const handleGroupChecked = () => {
    const allChecked = checkedAssignments
      .filter(a => a.assignment.status === 'created')
      .every(a => a.checked);
    setCheckedAssignments(prev =>
      prev.map(a =>
        a.assignment.status === 'created' ? { ...a, checked: !allChecked } : a
      )
    );
  };

  const handleAssignmentChecked = (id: number, checked: boolean) => {
    setCheckedAssignments(prevState =>
      prevState.map(a => (a.assignment.id === id ? { ...a, checked } : a))
    );
  };

  const checkGroupSymbol = () => {
    const checkedCount = checkedAssignments.filter(a => a.checked).length;
    if (checkedCount === 0) {
      return false;
    }
    if (
      checkedCount ===
      checkedAssignments.filter(a => a.assignment.status === 'created').length
    ) {
      return true;
    }
    return 'indeterminate';
  };

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
      <div className={'flex flex-row items-center gap-4 self-stretch'}>
        {checkedAssignments && (
          <Checkbox
            checked={checkGroupSymbol()}
            onCheckedChange={handleGroupChecked}
            disabled={props.groupAssignments.every(
              a => a.assignment.status !== 'created'
            )}
          ></Checkbox>
        )}
        <h2 className={'text-xl font-bold'}>
          {props.assignmentGroup} ({props.groupAssignments.length})
        </h2>
      </div>
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
      <div className={'grid grid-cols-1 @6xl:grid-cols-2 gap-2 self-stretch'}>
        {checkedAssignments &&
          checkedAssignments.map(assignment => (
            <AssignmentCard
              assignment={assignment.assignment}
              checked={assignment.checked}
              handleChange={checked =>
                handleAssignmentChecked(assignment.assignment.id, checked)
              }
              key={assignment.assignment.id}
            />
          ))}
      </div>
      {checkedAssignments && (
        <Tooltip open={!checkedAssignments.some(a => a.checked) ? null : false}>
          <TooltipTrigger
            render={
              <span className="inline-block">
                <Button
                  className={'ml-auto'}
                  disabled={!checkedAssignments.some(a => a.checked)}
                  onClick={() => setOpenReleaseDialog(true)}
                >
                  Release
                </Button>
              </span>
            }
          ></TooltipTrigger>
          <TooltipContent>
            <p>No assignments are selected.</p>
          </TooltipContent>
        </Tooltip>
      )}
      {openReleaseDialog && (
        <ReleaseDialog
          assignments={checkedAssignments}
          lectureId={props.lectureId}
          openDialog={openReleaseDialog}
          setOpenDialog={setOpenReleaseDialog}
          groupName={props.assignmentGroup}
          handleGroupChecked={handleGroupChecked}
          handleAssignmentChecked={handleAssignmentChecked}
          checkGroupSymbol={checkGroupSymbol}
        />
      )}
    </div>
  );
};
