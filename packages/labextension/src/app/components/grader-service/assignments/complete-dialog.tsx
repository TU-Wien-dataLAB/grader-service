import React from 'react';
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle
} from '../../../shadcn-components/ui/dialog';
import { Assignment } from '../../../../model/assignment';
import { Button } from '../../../shadcn-components/ui/button';
import { useAssignmentStatus } from '../../../hooks/assignment/assignment-status-hook';

interface IDeleteDialog {
  assignment: Assignment;
  lectureId: number;
  openDialog: boolean;
  setOpenDialog: React.Dispatch<React.SetStateAction<boolean>>;
}

export const CompleteDialog = (props: IDeleteDialog) => {
  const { handleComplete } = useAssignmentStatus();
  return (
    <Dialog open={props.openDialog} onOpenChange={props.setOpenDialog}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Complete assignment</DialogTitle>
        </DialogHeader>
        <div
          className={
            'flex flex-col p-6 gap-4 items-start self-stretch border-t border-border break-all'
          }
        >
          <p>
            Do you want to mark "
            <span className={'font-bold'}>{props.assignment.name}</span>"{' '}
            complete? This action will hide the assignment for all students.
          </p>
        </div>
        <DialogFooter>
          <Button
            type={'button'}
            onClick={() => {
              props.setOpenDialog(false);
              handleComplete(props.assignment, props.lectureId);
            }}
          >
            Complete
          </Button>
          <Button
            type={'button'}
            variant={'outline'}
            onClick={() => props.setOpenDialog(false)}
            autoFocus
          >
            Cancel
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
