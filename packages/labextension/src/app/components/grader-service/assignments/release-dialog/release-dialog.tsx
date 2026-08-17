import React from 'react';
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle
} from '../../../../shadcn-components/ui/dialog';
import { Assignment } from '../../../../../model/assignment';
import { Field, FieldGroup } from '../../../../shadcn-components/ui/field';
import { Label } from '../../../../shadcn-components/ui/label';
import { Button } from '../../../../shadcn-components/ui/button';
import { useForm } from '@tanstack/react-form';
import {
  IAssignmentChecked,
  IGroupedAssignments
} from '../../../../pages/instructor-view/lecture';
import { useAssignmentStatus } from '../../../../hooks/assignment/assignment-status-hook';
import { Textarea } from '../../../../shadcn-components/ui/textarea';
import AssignmentGroupedCheckboxList from './grouped-assignments-checkbox-list';

interface IReleaseDialog {
  assignments: Assignment | IAssignmentChecked[] | IGroupedAssignments;
  groupName?: string;
  isAssignmentsGrouped?: boolean;
  lectureId: number;
  openDialog: boolean;
  setOpenDialog: React.Dispatch<React.SetStateAction<boolean>>;
  handleGroupChecked?: (group: string) => void;
  handleAssignmentChecked?: (
    id: number,
    checked: boolean,
    group: string
  ) => void;
  checkGroupSymbol?: (group: string) => boolean | 'indeterminate';
}

export const ReleaseDialog = (props: IReleaseDialog) => {
  const { handleRelease, handleAssignmentsRelease } = useAssignmentStatus();
  const form = useForm({
    defaultValues: {
      comment: 'Release'
    },
    onSubmit: async ({ value }) => {
      if (props.isAssignmentsGrouped) {
        const flatAssignments = Object.values(props.assignments).flat();
        await handleAssignmentsRelease(flatAssignments, props.lectureId);
      }
      if (Array.isArray(props.assignments)) {
        await handleAssignmentsRelease(props.assignments, props.lectureId);
      } else {
        await handleRelease(props.assignments, props.lectureId);
      }
      props.setOpenDialog(false);
    }
  });

  const renderGroups: [string, IAssignmentChecked[]][] = props.assignments
    ? props.isAssignmentsGrouped
      ? Object.entries(props.assignments)
      : [[props.groupName, props.assignments]]
    : [];

  const getDialogTitle = () => {
    if (!props.assignments) {
      return 'Release assignments';
    }

    if (props.isAssignmentsGrouped || Array.isArray(props.assignments)) {
      return 'Release assignments';
    }

    if (typeof props.assignments === 'object' && props.assignments.name) {
      return `Release ${props.assignments.name}`;
    }

    return 'Release assignments';
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
            <DialogTitle>{getDialogTitle()}</DialogTitle>
          </DialogHeader>
          <FieldGroup
            className={
              'flex flex-col p-6 gap-4 items-start self-stretch border-t border-border'
            }
          >
            {renderGroups.map(([groupKey, assignments]) => (
              <AssignmentGroupedCheckboxList
                key={groupKey}
                assignments={assignments}
                groupName={groupKey}
                checkGroupSymbol={props.checkGroupSymbol}
                handleGroupChecked={props.handleGroupChecked}
                handleAssignmentChecked={props.handleAssignmentChecked}
              />
            ))}
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

export default ReleaseDialog;
