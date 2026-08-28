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
import { useAssignmentDelete } from '../../../hooks/assignment/assignment-delete-hook';

interface IDeleteDialog {
  assignment: Assignment;
  lectureId: number;
  openDialog: boolean;
  setOpenDialog: React.Dispatch<React.SetStateAction<boolean>>;
}

export const DeleteDialog = (props: IDeleteDialog) => {
  const { handleDeleteAssignment } = useAssignmentDelete();
  return (
    <Dialog open={props.openDialog} onOpenChange={props.setOpenDialog}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Delete assignment</DialogTitle>
        </DialogHeader>
        <div
          className={
            'flex flex-col p-6 gap-4 items-start self-stretch border-t border-border break-all'
          }
        >
          <p className="w-full">
            Are you sure you want to delete "
            <span className={'font-bold'}>{props.assignment.name}</span>
            "? This action cannot be undone and all related data will be
            permanently removed.
          </p>
        </div>
        <DialogFooter>
          <Button
            type={'button'}
            variant={'destructive'}
            interactive={false}
            onClick={() => {
              props.setOpenDialog(false);
              handleDeleteAssignment(props.assignment.id, props.lectureId);
            }}
          >
            Delete permanently
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
