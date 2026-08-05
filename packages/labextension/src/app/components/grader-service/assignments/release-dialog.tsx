import React from 'react';
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle
} from '../../../shadcn-components/ui/dialog';
import { Assignment } from '../../../../model/assignment';
import { Field, FieldGroup } from '../../../shadcn-components/ui/field';
import { Label } from '../../../shadcn-components/ui/label';
import { Button } from '../../../shadcn-components/ui/button';
import { useForm } from '@tanstack/react-form';
import { IAssignmentChecked } from '../../../pages/instructor-view/lecture';
import { useAssignmentStatus } from '../../../hooks/assignment/assignment-status-hook';
import { Checkbox } from '../../../shadcn-components/ui/checkbox';
import { CornerDownRight } from 'lucide-react';
import { Textarea } from '../../../shadcn-components/ui/textarea';
import {
  CreatedAssignmentBadge,
  ReleasedAssignmentBadge
} from '../../ui/badges';
import { Badge } from '../../../shadcn-components/ui/badge';

interface IReleaseDialog {
  assignments: Assignment | IAssignmentChecked[];
  lectureId: number;
  openDialog: boolean;
  setOpenDialog: React.Dispatch<React.SetStateAction<boolean>>;
  groupName?: string;
  handleGroupChecked?: () => void;
  handleAssignmentChecked?: (id: number, checked: boolean) => void;
  checkGroupSymbol?: () => boolean | 'indeterminate';
}

export const ReleaseDialog = (props: IReleaseDialog) => {
  const { handleRelease, handleAssignmentsRelease } = useAssignmentStatus();
  const form = useForm({
    defaultValues: {
      comment: 'Release'
    },
    onSubmit: ({ value }) => {
      if (Array.isArray(props.assignments)) {
        handleAssignmentsRelease(props.assignments, props.lectureId);
      } else {
        handleRelease(props.assignments, props.lectureId);
      }
      props.setOpenDialog(false);
    }
  });
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
        return <Badge>Completed</Badge>;
    }
  };

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
              <DialogTitle>Release assignments</DialogTitle>
            ) : (
              <DialogTitle>Release {props.assignments.name}</DialogTitle>
            )}
          </DialogHeader>
          <FieldGroup
            className={
              'flex flex-col p-6 gap-4 items-start self-stretch border-t border-border'
            }
          >
            {Array.isArray(props.assignments) && (
              <div className={'flex flex-col items-start w-full max-h-80'}>
                <div
                  className={'inline-flex min-h-8 items-start rounded-xs gap-2'}
                >
                  <Checkbox
                    checked={props.checkGroupSymbol?.() ?? false}
                    onCheckedChange={props.handleGroupChecked}
                  />
                  <Label>{props.groupName}</Label>
                </div>
                <ul className={'w-full overflow-y-auto'}>
                  {props.assignments.map(a => (
                    <li
                      key={a.assignment.id}
                      className={'flex min-h-8 items-center gap-2'}
                    >
                      <CornerDownRight
                        className={'size-4 text-border shrink-0'}
                      />
                      <Checkbox
                        checked={a.checked}
                        disabled={a.assignment.status !== 'created'}
                        onCheckedChange={() =>
                          props.handleAssignmentChecked?.(
                            a.assignment.id,
                            !a.checked
                          )
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
                      <div className={'ml-auto'}>
                        {assignmentStatus(a.assignment)}
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            <form.Field
              name={'comment'}
              validators={{
                onChange: ({ value }) => {
                  if (value.trim().length > 255) {
                    return 'Comment is too long.';
                  } else if (value.trim().length === 0) {
                    return 'Comment is empty.';
                  }
                  return undefined;
                }
              }}
              children={field => {
                return (
                  <Field data-invalid={!field.state.meta.isValid}>
                    <Label htmlFor={'comment'}>Comment</Label>
                    <Textarea
                      id={'comment'}
                      defaultValue={'Release'}
                      onChange={e => field.handleChange(e.target.value)}
                    ></Textarea>
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
              Release
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
