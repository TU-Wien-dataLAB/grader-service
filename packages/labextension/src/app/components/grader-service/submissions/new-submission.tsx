import React, { useState } from 'react';
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

type TProps = {
  setShowNewSubmissionForm: (val: boolean) => void;
};

const NewSubmission = (props: TProps) => {
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set());
  const selectOptions = [
    { value: 'nadja', label: 'Nadja' },
    { value: 'florian', label: 'Florian' }
  ];

  const submissionFileOptions = [
    { value: 'file.py1', label: 'file.py1', checked: false },
    { value: 'file.py2', label: 'file.py2', checked: true },
    { value: 'file.py3', label: 'file.py3', checked: true }
  ];

  const form = useForm({
    defaultValues: {
      student: ''
    },
    onSubmit: async ({ value }) => {
      console.log(value);
    }
  });

  const onFileSelection = (fileId: string) => {
    setSelectedFiles(prev => {
      const updated = new Set(prev);
      if (selectedFiles.has(fileId)) {
        updated.delete(fileId);
      } else {
        updated.add(fileId);
      }
      return updated;
    });
  };

  return (
    <div className={'flex flex-col items-start gap-4 self-stretch'}>
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
          <form.Field
            name={'student'}
            children={field => (
              <Field id={'select-field'}>
                <Label htmlFor={field.name}>Student *</Label>
                <Select
                  name={field.name}
                  items={selectOptions}
                  onValueChange={value => field.handleChange(value as string)}
                  required
                >
                  <SelectTrigger className={'bg-white'}>
                    <SelectValue
                      placeholder={
                        field.state.value === 'active' ? 'Active' : 'Completed'
                      }
                    />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectGroup>
                      {selectOptions.map(({ label, value }) => (
                        <SelectItem key={value} value={value}>
                          {label}
                        </SelectItem>
                      ))}
                    </SelectGroup>
                  </SelectContent>
                </Select>
              </Field>
            )}
          ></form.Field>
          <div>
            <p className="font-bold">Notebooks & files upload *</p>
            <p>
              Start uploading your notebooks & files in the file browser on the
              left.
            </p>
          </div>
          <div>
            <p className="font-bold">Submission files *</p>
            <p>Select the notebooks & files to include in your submission.</p>
            <ul className={'w-full overflow-y-auto'}>
              {submissionFileOptions.map(file => (
                <li className={'flex min-h-8 items-center gap-2'}>
                  <Checkbox
                    onCheckedChange={e => onFileSelection(file.value)}
                    checked={selectedFiles.has(file.value)}
                  />
                  <p>{file.label}</p>
                </li>
              ))}
            </ul>
          </div>
          <div className="flex gap-4">
            <Button type="submit">Create submission</Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => props.setShowNewSubmissionForm(false)}
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
