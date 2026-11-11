import React from 'react';
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle
} from '../../../shadcn-components/ui/dialog';
import { Button } from '../../../shadcn-components/ui/button';

interface IRestoreSubmissionDialog {
  openDialog: boolean;
  setOpenDialog: React.Dispatch<React.SetStateAction<boolean>>;
  handleRestoreSubmission: () => void;
}

export const RestoreSubmissionDialog = (props: IRestoreSubmissionDialog) => {
  return (
    <Dialog open={props.openDialog} onOpenChange={props.setOpenDialog}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Restore latest submission</DialogTitle>
        </DialogHeader>
        <div
          className={
            'flex flex-col p-6 gap-4 items-start self-stretch border-t border-border break-all'
          }
        >
          <p className="w-full">
            Are you sure you want to restore the lastest submission? All changes
            will be discarded, and the submission will be restored to its
            original state.
          </p>
        </div>
        <DialogFooter>
          <Button
            type={'button'}
            variant="default"
            interactive={false}
            onClick={() => {
              props.setOpenDialog(false);
              props.handleRestoreSubmission();
            }}
          >
            Restore latest submission
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
