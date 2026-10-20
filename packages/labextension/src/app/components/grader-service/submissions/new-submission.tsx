import React from 'react';
import { Field } from '../../../shadcn-components/ui/field';
import { Label } from '../../../shadcn-components/ui/label';
import { useForm } from '@tanstack/react-form';
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
import { useParams } from 'react-router';
import { useMutation, useQuery } from '@tanstack/react-query';
import { lectureUsersQuery } from '../../../../services/queries/lectures.queries';
import { useFiles } from '../../../hooks/submissions/get-uploaded-files-hook';
import { createSubmissionFiles } from '../../../../services/git.service';
import { ErrorBanner } from '../../ui/error-banner';
import { OctagonAlert } from 'lucide-react';
import { useMutationStatus } from '../../../../widget';

type TProps = {
  setOpenNewSubmission: (val: boolean) => void;
  currentPath: string;
};

const NewSubmission = (props: TProps) => {
  const params = useParams();
  const lectureId = Number(params.lid);
  const assignmentId = Number(params.aid);
  const { data: lectureUsers } = useQuery(lectureUsersQuery(lectureId));
  const { status, setStatus } = useMutationStatus();

  const path = props.currentPath;
  const cleanedPath = path.endsWith('/') ? path.slice(0, -1) : path;
  const { data: files } = useFiles(cleanedPath);

  const lectureUsersOptions = lectureUsers?.students.map(student => {
    return { label: student.display_name, value: student.name };
  });

  const submissionFileOptions =
    files && files.length > 0
      ? files.map(file => {
          return { value: file.path, label: file.name, checked: false };
        })
      : [];

  type submissionFields = {
    student: string;
    files: string[];
  };

  const createSubmissionMutation = useMutation({
    mutationFn: async (values: submissionFields) => {
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
      props.setOpenNewSubmission(false);
    },
    onError: () => {
      setStatus({
        message: 'Failed to create a submission. Please, try again!',
        status: 'error'
      });
    }
  });

  const form = useForm({
    defaultValues: {
      student: '',
      files: []
    },
    onSubmit: async ({ value }) => {
      await createSubmissionMutation.mutateAsync(value);
    }
  });

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
            {submissionFileOptions.length === 0 && (
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
          {submissionFileOptions.length > 0 && (
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
                      {submissionFileOptions.map(opt => {
                        const id = `${field.name}-${opt.value}`;
                        return (
                          <div
                            key={opt.value}
                            className={'flex min-h-8 items-center gap-2'}
                          >
                            <Checkbox
                              id={id}
                              checked={field.state.value.includes(opt.value)}
                              onBlur={field.handleBlur}
                              onCheckedChange={checked => {
                                field.handleChange(
                                  checked === true
                                    ? [...field.state.value, opt.value]
                                    : field.state.value.filter(
                                        (v: string) => v !== opt.value
                                      )
                                );
                              }}
                              className={`${!field.state.meta.isValid && 'border border-[#DC182C]'}`}
                            />
                            <Label className="font-normal" htmlFor={id}>
                              {opt.label}
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
              onClick={() => props.setOpenNewSubmission(false)}
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
