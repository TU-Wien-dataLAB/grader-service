import React, { useEffect, useMemo } from 'react';
import { Field } from '../../../shadcn-components/ui/field';
import { Label } from '../../../shadcn-components/ui/label';
import { useForm, useSelector } from '@tanstack/react-form';
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '../../../shadcn-components/ui/select';
import { Button } from '../../../shadcn-components/ui/button';
import { Checkbox } from '../../../shadcn-components/ui/checkbox';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  lectureQuery,
  lectureUsersQuery
} from '../../../../services/queries/lectures.queries';
import { createSubmissionFiles } from '../../../../services/git.service';
import { ErrorBanner } from '../../ui/error-banner';
import { OctagonAlert } from 'lucide-react';
import { useMutationStatus } from '../../../../widget';
import {
  lectureBasePath,
  openInFileBrowser
} from '../../../../services/local-file.service';
import { useFiles } from '../../../hooks/submissions/get-uploaded-files-hook';

type submissionFields = {
  student: string;
  files: string[];
};

type TProps = {
  setOpenNewSubmission: (val: boolean) => void;
  lectureId: number;
  assignmentId: number;
};

const NewSubmission = (props: TProps) => {
  const { lectureId, assignmentId, setOpenNewSubmission } = props;

  const { data: lectureUsers } = useQuery(lectureUsersQuery(lectureId));
  const { data: lecture } = useQuery(lectureQuery(lectureId));
  const { status, setStatus } = useMutationStatus();
  const queryClient = useQueryClient();

  const form = useForm({
    defaultValues: {
      student: '',
      files: []
    },
    onSubmit: async ({ value }) => {
      await createSubmissionMutation.mutateAsync(value);
    }
  });

  const userDir = useSelector(form.store, state => state.values.student);

  const path = useMemo(
    () => `${lectureBasePath}${lecture.code}/create/${assignmentId}/${userDir}`,
    [lecture, assignmentId, userDir]
  );

  const { data: files = [] } = useFiles(path);

  const lectureUsersOptions = useMemo(() => {
    return lectureUsers?.students.map(student => {
      return { label: student.display_name, value: student.name };
    });
  }, [lectureUsers]);

  const createSubmissionMutation = useMutation({
    mutationFn: async (values: submissionFields) => {
      console.log('selected files: ', values.files);
      await createSubmissionFiles(
        lectureId,
        assignmentId,
        values.student,
        values.files
      );
    },
    onSuccess: () => {
      setStatus({
        message: 'You successfully created a new submission.',
        status: 'success'
      });
      setOpenNewSubmission(false);
      queryClient.invalidateQueries({ queryKey: ['submissions'] });
    },
    onError: () => {
      setStatus({
        message: 'Failed to create a submission. Please, try again!',
        status: 'error'
      });
    }
  });

  useEffect(() => {
    openInFileBrowser(path);
  }, [path]);

  return (
    <div className={'flex flex-col items-start gap-4 self-stretch'}>
      {status.status === 'error' && <ErrorBanner message={status.message} />}
      <h2 className={'text-xl font-bold'}>New submission</h2>
      <div className="sm:max-w-186 w-full">
        <form
          className={'flex flex-col gap-4'}
          id={'edit-lecture-form'}
          onSubmit={event => {
            event.preventDefault();
            form.handleSubmit();
          }}
        >
          <form.Subscribe
            selector={state => ({
              isValid: state.isValid,
              submissionAttempts: state.submissionAttempts
            })}
          >
            {({ isValid, submissionAttempts }) =>
              submissionAttempts > 0 && !isValid ? (
                <div className="my-6">
                  <ErrorBanner
                    title="Error: Required information missing"
                    message="Some required fields have not been completed. Fill in the missing information to continue."
                  />
                </div>
              ) : null
            }
          </form.Subscribe>
          <form.Field
            name="student"
            validators={{
              onSubmit: ({ value }) => (!value ? 'Select an option.' : null)
            }}
            children={field => (
              <Field id={'select-field'}>
                <Label className="font-bold" htmlFor={field.name}>
                  Student *
                </Label>
                <Select
                  name={field.name}
                  items={lectureUsersOptions}
                  onValueChange={value => field.handleChange(value as string)}
                >
                  <SelectTrigger
                    className={`bg-white ${!field.state.meta.isValid && 'border border-[#DC182C]'}`}
                  >
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectGroup>
                      {lectureUsersOptions?.map(({ label, value }) => (
                        <SelectItem key={value} value={value}>
                          {label}
                        </SelectItem>
                      ))}
                    </SelectGroup>
                  </SelectContent>
                </Select>
                {!field.state.meta.isValid ? (
                  <div
                    className="text-[#DC182C] flex items-center gap-2"
                    role="alert"
                  >
                    <OctagonAlert
                      width={4}
                      height={4}
                      size={4}
                      className={'text-[#DC182C] size-6'}
                    />
                    <span>{field.state.meta.errors.join(', ')}</span>
                  </div>
                ) : null}
              </Field>
            )}
          ></form.Field>
          <div>
            <p className="font-bold py-1">Notebooks & files upload *</p>
            <p className="py-1">
              Start uploading your notebooks & files in the file browser on the
              left.
            </p>
            {files.length === 0 && (
              <div
                className="text-[#DC182C] flex items-center gap-2"
                role="alert"
              >
                <OctagonAlert
                  width={4}
                  height={4}
                  size={4}
                  className={'text-[#DC182C] size-6'}
                />
                <span>Upload a file.</span>
              </div>
            )}
          </div>
          {files.length > 0 && (
            <div>
              <p className="font-bold py-1">Submission files *</p>
              <form.Field
                name="files"
                validators={{
                  onChange: ({ value }) =>
                    value.length === 0
                      ? 'Select this option to continue.'
                      : undefined
                }}
              >
                {field => (
                  <fieldset className="space-y-2">
                    <legend className="py-1">
                      Select the notebooks & files to include in your
                      submission.
                    </legend>
                    <div className={'w-full overflow-y-auto'}>
                      {files.map(opt => {
                        const id = `${field.name}-${opt.path}`;
                        return (
                          <div
                            key={opt.path}
                            className={'flex min-h-8 items-center gap-2'}
                          >
                            <Checkbox
                              id={id}
                              checked={field.state.value.includes(opt.name)}
                              onBlur={field.handleBlur}
                              onCheckedChange={checked => {
                                field.handleChange(
                                  checked === true
                                    ? [...field.state.value, opt.name]
                                    : field.state.value.filter(
                                        (v: string) => v !== opt.name
                                      )
                                );
                              }}
                              className={`${!field.state.meta.isValid && 'border border-[#DC182C]'}`}
                            />
                            <Label className="font-normal" htmlFor={id}>
                              {opt.name}
                            </Label>
                          </div>
                        );
                      })}
                    </div>
                    {field.state.meta.errors.length > 0 && (
                      <p role="alert" className="text-sm text-destructive">
                        {field.state.meta.errors.join(', ')}
                      </p>
                    )}
                  </fieldset>
                )}
              </form.Field>
            </div>
          )}

          <div className="flex gap-4">
            <Button type="submit">Create submission</Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => setOpenNewSubmission(false)}
            >
              Cancel
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default NewSubmission;
