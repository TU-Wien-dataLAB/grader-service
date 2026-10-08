import React from 'react';
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle
} from '../../../shadcn-components/ui/dialog';
import { Button } from '../../../shadcn-components/ui/button';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger
} from '../../../shadcn-components/ui/accordion';
import {
  extractRelativePaths,
  IFile
} from '../../../../services/local-file.service';
import { RowSelectionState } from '@tanstack/react-table';
import { Textarea } from '../../../shadcn-components/ui/textarea';
import { Field, FieldLabel } from '../../../shadcn-components/ui/field';
import { Label } from '../../../shadcn-components/ui/label';
import { Checkbox } from '../../../shadcn-components/ui/checkbox';
import { pushAssignment } from '../../../../services/git.service';
import { RepoType } from '../../utils/repo-type';
import { useForm } from '@tanstack/react-form';
import { useMutationStatus } from '../../../../widget';
import { HTTPError } from '../../../../services/request.service';
import { Lecture } from '../../../../model/lecture';
import { CornerDownRight } from 'lucide-react';
import { RefetchOptions } from '@tanstack/react-query';

interface ISaveFilesDialogProps {
  isOpen: boolean;
  setIsOpen: (isOpen: boolean) => void;
  selectedRows: RowSelectionState;
  files: IFile[];
  lecture: Lecture;
  assignmentId: number;
  refetchFiles: (options?: RefetchOptions) => void;
}
// non-recursive version of IFile, just for the form
type SelectedFile = Omit<IFile, 'content'> & { content?: unknown };
export const SaveFilesDialog = (props: ISaveFilesDialogProps) => {
  const { setStatus } = useMutationStatus();
  const flatten = (file: IFile): IFile[] =>
    file.type === 'directory'
      ? [file, ...(file.content ?? []).flatMap(flatten)]
      : [file];

  const form = useForm({
    defaultValues: {
      comment: '',
      selectedPaths: props.files
        .flatMap(flatten)
        .filter(file => !!props.selectedRows?.[file.path]) as SelectedFile[]
    },
    onSubmit: async ({ value }) => {
      const files = value.selectedPaths as IFile[];
      const relativePaths = Array.from(
        new Set(
          files.flatMap(f =>
            extractRelativePaths(
              props.lecture.code,
              RepoType.SOURCE,
              props.assignmentId,
              f
            )
          )
        )
      );
      try {
        await Promise.all([
          pushAssignment(
            props.lecture.id,
            props.assignmentId,
            RepoType.SOURCE,
            value.comment,
            relativePaths
          ),
          pushAssignment(
            props.lecture.id,
            props.assignmentId,
            RepoType.RELEASE,
            value.comment,
            relativePaths
          )
        ])
          .then(() => {
            setStatus({
              message:
                'Your changes have been saved successfully. The notebooks & files will now be pushed to the repository, and the updates will be visible to your students.',
              status: 'success'
            });
            props.setIsOpen(false);
          })
          .catch((err: HTTPError) => {
            setStatus({ message: err.message, status: 'error' });
          });
        props.refetchFiles();
      } catch (err) {
        setStatus({ message: 'Error saving assignment', status: 'error' });
      }
    }
  });

  return (
    <Dialog open={props.isOpen} onOpenChange={props.setIsOpen}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Save notebooks & files</DialogTitle>
        </DialogHeader>
        <div
          className={
            'flex p-6 flex-col items-start gap-4 self-stretch border-t border-border'
          }
        >
          <form
            id={'save-files-dialog-form'}
            className={'self-stretch'}
            onSubmit={e => {
              e.preventDefault();
              form.handleSubmit();
            }}
          >
            <form.Field
              name="selectedPaths"
              validators={{
                onChange: ({ value }) => {
                  if (value?.length === 0) {
                    return 'Please select at least one file.';
                  }
                  return undefined;
                }
              }}
            >
              {field => {
                const files = field.state.value as IFile[];
                const selected = new Set(files);
                const hasSelection = (file: IFile): boolean =>
                  selected.has(file) ||
                  (file.type === 'directory' &&
                    (file.content ?? []).some(hasSelection));

                const selectedFileTrees = props.files.filter(hasSelection);
                const unselectedFileTrees = props.files.filter(
                  f => !hasSelection(f)
                );

                const toggle = (file: IFile, isChecked: boolean) =>
                  field.handleChange((prev: SelectedFile[]) => {
                    const without = prev.filter(f => f.path !== file.path);
                    return isChecked ? [...without, file] : without;
                  });

                const renderRow = (file: IFile, depth = 0): React.ReactNode => {
                  return (
                    <>
                      <div
                        key={file.path}
                        className="flex items-center gap-2 self-stretch"
                      >
                        {depth > 0 && (
                          <CornerDownRight className="size-4 text-border" />
                        )}
                        <Checkbox
                          checked={selected.has(file)}
                          onCheckedChange={checked => toggle(file, !!checked)}
                        />
                        <p>{file.name}</p>
                      </div>
                      {file.type === 'directory' &&
                        file.content?.length > 0 && (
                          <div
                            className={`${
                              depth > 0 ? 'ml-6' : 'ml-1'
                            } flex flex-col gap-2`}
                          >
                            {file.content.map(file =>
                              renderRow(file, depth + 1)
                            )}
                          </div>
                        )}
                    </>
                  );
                };
                return (
                  <div className={'flex flex-col gap-4 self-stretch'}>
                    <Field className="flex flex-col items-start gap-2">
                      <Label>Selected notebooks & files</Label>
                      <div className="flex flex-col items-start self-stretch gap-1">
                        {selectedFileTrees.map(file => renderRow(file, 0))}
                      </div>
                      {!field.state.meta.isValid && (
                        <em role={'alertdialog'} className={'text-red-700'}>
                          {field.state.meta.errors.join(', ')}
                        </em>
                      )}
                    </Field>

                    {unselectedFileTrees.length > 0 && (
                      <Accordion>
                        <AccordionItem value="unselected-files">
                          <AccordionTrigger>
                            Unselected notebooks & files
                          </AccordionTrigger>
                          <AccordionContent className="flex max-h-100 overflow-y-scroll p-4 flex-col items-start self-stretch border-primary border-l-2 bg-[#F5F5F5] gap-1">
                            {unselectedFileTrees.map(file =>
                              renderRow(file, 0)
                            )}
                          </AccordionContent>
                        </AccordionItem>
                      </Accordion>
                    )}
                  </div>
                );
              }}
            </form.Field>
            <form.Field
              name={'comment'}
              validators={{
                onChange: ({ value }) => {
                  if (value.trim().length === 0) {
                    return 'Comment is empty.';
                  }
                }
              }}
              children={field => (
                <Field>
                  <FieldLabel htmlFor={field.name}>Comment</FieldLabel>
                  <Textarea
                    id={field.name}
                    name={field.name}
                    value={field.state?.value}
                    required
                    onChange={e => field.handleChange(e.target.value)}
                  />
                  {!field.state.meta.isValid && (
                    <em role={'alertdialog'} className={'text-red-700'}>
                      {field.state.meta.errors.join(', ')}
                    </em>
                  )}
                </Field>
              )}
            />
          </form>
        </div>
        <DialogFooter>
          <Button
            type={'submit'}
            form={'save-files-dialog-form'}
            disabled={!form.state.isValid}
          >
            Save
          </Button>
          <DialogClose render={<Button variant={'outline'}>Cancel</Button>}>
            Cancel
          </DialogClose>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
