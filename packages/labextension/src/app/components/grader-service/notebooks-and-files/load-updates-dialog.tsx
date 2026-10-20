import React from 'react';
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle
} from '../../../shadcn-components/ui/dialog';
import { Button } from '../../../shadcn-components/ui/button';
import { pullAssignment } from '../../../../services/git.service';
import { RepoType } from '../../utils/repo-type';
import { queryClient, useMutationStatus } from '../../../../widget';
import { HTTPError } from '../../../../services/request.service';
import { Lecture } from '../../../../model/lecture';

interface ILoadUpdatesDialogProps {
  lecture: Lecture;
  assignmentId: number;
  selectedDir: string;
  isOpen: boolean;
  setIsOpen: (isOpen: boolean) => void;
}

export const LoadUpdatesDialog = (props: ILoadUpdatesDialogProps) => {
  const { setStatus } = useMutationStatus();
  const handlePullAssignment = async () => {
    try {
      await pullAssignment(
        props.lecture.id,
        props.assignmentId,
        props.selectedDir === 'source' ? RepoType.SOURCE : RepoType.RELEASE
      )
        .then(async () => {
          props.setIsOpen(false);
          await Promise.all([
            queryClient.invalidateQueries({
              queryKey: [
                'files',
                props.lecture.code,
                props.assignmentId,
                props.selectedDir
              ]
            }),
            queryClient.invalidateQueries({
              queryKey: [
                'remote-repo-status',
                props.lecture.code,
                props.assignmentId,
                props.selectedDir
              ]
            })
          ]);
        })
        .catch((err: HTTPError) =>
          setStatus({ message: err.message, status: 'error' })
        );
    } catch (err) {
      setStatus({ message: 'Failed to update assignment!', status: 'error' });
    }
  };
  return (
    <Dialog open={props.isOpen} onOpenChange={props.setIsOpen}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Confirm loading updates</DialogTitle>
        </DialogHeader>
        <div
          className={
            'flex flex-col gap-4 p-6 items-start self-stretch border-t border-border'
          }
        >
          <p>
            Are you sure you want to load the latest updates? This will
            overwrite your current changes.
          </p>
        </div>
        <DialogFooter showCloseButton>
          <Button onClick={() => handlePullAssignment()}>Confirm</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
