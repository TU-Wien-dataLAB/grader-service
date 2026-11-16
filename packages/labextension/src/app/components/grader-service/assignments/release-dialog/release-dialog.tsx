import React from 'react';
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
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
import { useAssignmentRemoteStatus } from '../../../../hooks/assignment/assignment-remote-status-hook';
import { Textarea } from '../../../../shadcn-components/ui/textarea';
import AssignmentGroupedCheckboxList from './grouped-assignments-checkbox-list';
import { AssignmentReleaseRemoteStatusBadge } from '../utils/assignment-release-remote-status-badge';
import { RemoteFileStatus } from '../../../../../model/remoteFileStatus';

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
  isAnyAssignmentChecked?: boolean;
}

const dialogDescriptions: Record<RemoteFileStatus, string> = {
  unsaved_changes:
    "Your local changes haven't been saved. The released assignment will not include them.",
  divergent:
    'Your local changes are out of sync with the remote system. Please resolve the conflicts before releasing.',
  update_needed:
    'The assignment has been updated in the remote system. ' +
    "The release will be done using the files from remote. You can go back to 'Notebooks and files' of this assignment and load the updates to see what would be released.",
  up_to_date: '',
  no_backup: ''
};

export const ReleaseDialog = (props: IReleaseDialog) => {
  const { handleRelease, handleAssignmentsRelease } = useAssignmentStatus();

  /* the dialog either shows a single assignment, a list of checked
     assignments or all assignments grouped by their group */
  const singleAssignment =
    !props.isAssignmentsGrouped && !Array.isArray(props.assignments)
      ? (props.assignments as Assignment)
      : undefined;

  const form = useForm({
    defaultValues: {
      comment: 'Release'
    },
    onSubmit: ({ value }) => {
      if (props.isAssignmentsGrouped) {
        const flatAssignments = Object.values(
          props.assignments as IGroupedAssignments
        ).flat();
        handleAssignmentsRelease(flatAssignments, props.lectureId);
      } else if (Array.isArray(props.assignments)) {
        handleAssignmentsRelease(props.assignments, props.lectureId);
      } else if (singleAssignment) {
        handleRelease(singleAssignment, props.lectureId);
      }
      props.setOpenDialog(false);
    }
  });

  const renderGroups: [string, IAssignmentChecked[]][] =
    props.isAssignmentsGrouped
      ? Object.entries((props.assignments as IGroupedAssignments) ?? {})
      : Array.isArray(props.assignments)
        ? [[props.groupName ?? '', props.assignments]]
        : [];

  const getDialogTitle = () => {
    if (props.isAssignmentsGrouped || Array.isArray(props.assignments)) {
      return 'Release assignments';
    }
    return `Release ${singleAssignment?.name}`;
  };

  /* file status handling needed for release action */
  const { filesLength, remoteStatus } = useAssignmentRemoteStatus(
    props.lectureId,
    singleAssignment?.id
  );

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
          <DialogHeader className="min-w-0 gap-2">
            <div className={'flex flex-row gap-2 items-center self-stretch'}>
              <DialogTitle className="truncate max-w-[calc(100%-4rem)]">
                {getDialogTitle()}
              </DialogTitle>
              {singleAssignment && (
                <AssignmentReleaseRemoteStatusBadge
                  remoteRepoStatus={remoteStatus}
                  filesLength={filesLength}
                />
              )}
            </div>
            {singleAssignment && (
              <DialogDescription>
                {dialogDescriptions[remoteStatus]}
              </DialogDescription>
            )}
          </DialogHeader>
          <FieldGroup
            className={
              'flex flex-col p-6 gap-4 items-start self-stretch border-t border-border'
            }
          >
            {(props.isAssignmentsGrouped || Array.isArray(props.assignments)) &&
              renderGroups.map(([groupKey, assignments]) => (
                <AssignmentGroupedCheckboxList
                  key={groupKey}
                  assignments={assignments}
                  groupName={groupKey}
                  lectureId={props.lectureId}
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
            <Button
              disabled={
                (props.isAssignmentsGrouped && !props.isAnyAssignmentChecked) ||
                (props.groupName && !!props.checkGroupSymbol(props.groupName))
              }
              type={'submit'}
              form={'release-dialog-form'}
            >
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
