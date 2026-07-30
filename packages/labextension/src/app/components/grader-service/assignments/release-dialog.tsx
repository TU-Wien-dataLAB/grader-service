import React from 'react';
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle
} from '../../../shadcn-components/ui/dialog';
import { Assignment } from '../../../../model/assignment';
import { Field, FieldGroup } from '../../../shadcn-components/ui/field';
import { Label } from '../../../shadcn-components/ui/label';
import { Input } from '../../../shadcn-components/ui/input';
import { Button } from '../../../shadcn-components/ui/button';
import { useForm } from '@tanstack/react-form';
import { IAssignmentChecked } from '../../../pages/instructor-view/lecture';
import { useAssignmentStatus } from '../../../hooks/assignment/assignment-status-hook';

interface IReleaseDialog {
  assignments: Assignment | IAssignmentChecked[];
  lectureId: number;
  openDialog: boolean;
  setOpenDialog: React.Dispatch<React.SetStateAction<boolean>>;
}

export const ReleaseDialog = (props: IReleaseDialog) => {
  const { handleRelease, handleAssignmentsRelease } = useAssignmentStatus();
  const form = useForm({
    defaultValues: {
      commitMessage: 'Release'
    },
    onSubmit: async ({ value }) => {
      if (Array.isArray(props.assignments)) {
        await handleAssignmentsRelease(props.assignments, props.lectureId);
      } else {
        await handleRelease(props.assignments, props.lectureId);
      }
      props.setOpenDialog(false);
    }
  });
  return (
    <Dialog open={props.openDialog} onOpenChange={props.setOpenDialog}>
      <form
        id={'release-dialog-form'}
        onSubmit={e => {
          e.preventDefault();
          form.handleSubmit();
        }}
      >
        <DialogContent>
          <DialogHeader>
            {Array.isArray(props.assignments) ? (
              <>
                <DialogTitle>Release following assignments:</DialogTitle>
                <DialogDescription>
                  <ul className={'list-disc ml-5'}>
                    {props.assignments.map(
                      a => a.checked && <li>{a.assignment.name}</li>
                    )}
                  </ul>
                </DialogDescription>
              </>
            ) : (
              <DialogTitle>Release {props.assignments.name}</DialogTitle>
            )}
          </DialogHeader>
          <FieldGroup
            className={
              'flex flex-col p-6 gap-4 items-start self-stretch border-t border-border'
            }
          >
            <form.Field
              name={'commitMessage'}
              validators={{
                onChange: ({ value }) => {
                  if (value.trim().length > 255) {
                    return 'Name is too long.';
                  } else if (value.trim().length === 0) {
                    return 'Name is empty.';
                  }
                  return undefined;
                }
              }}
              children={field => {
                return (
                  <Field data-invalid={!field.state.meta.isValid}>
                    <Label htmlFor={'commit-message'}>Commit message</Label>
                    <Input
                      id={'commit-message'}
                      defaultValue={'Release'}
                      onChange={e => field.handleChange(e.target.value)}
                    />
                    {!field.state.meta.isValid && (
                      <em role={'alertdialog'} className={'text-red-700'}>
                        {field.state.meta.errors.join(', ')}
                      </em>
                    )}
                  </Field>
                );
              }}
            ></form.Field>
          </FieldGroup>
          <DialogFooter>
            <Button type={'submit'} form={'release-dialog-form'}>
              Confirm
            </Button>
            <DialogClose>
              <Button
                variant={'outline'}
                onClick={() => props.setOpenDialog(false)}
              >
                Cancel
              </Button>
            </DialogClose>
          </DialogFooter>
        </DialogContent>
      </form>
    </Dialog>
  );
};
