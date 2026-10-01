import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger
} from '../../../shadcn-components/ui/dialog';
import { Field, FieldGroup } from '../../../shadcn-components/ui/field';
import { Label } from '../../../shadcn-components/ui/label';
import { Input } from '../../../shadcn-components/ui/input';
import { Button } from '../../../shadcn-components/ui/button';
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '../../../shadcn-components/ui/select';
import { useForm } from '@tanstack/react-form';
import { Lecture } from '../../../../model/lecture';
import { Pencil } from 'lucide-react';
import { useUpdateLecture } from '../../../hooks/lecture/update-lecture-hook';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger
} from '../../../shadcn-components/ui/tooltip';

interface IEditLectureDialog {
  lecture: Lecture;
}

export const EditLectureDialog = (props: IEditLectureDialog) => {
  const [openDialog, setOpenDialog] = useState(false);

  const { mutateLecture } = useUpdateLecture();

  const form = useForm({
    defaultValues: {
      name: props.lecture.name,
      status: props.lecture.complete ? 'completed' : 'active'
    },
    onSubmit: async ({ value }) => {
      // don't do anything if values haven't changed
      if (form.state.isPristine) {
        setOpenDialog(false);
        return;
      }
      await mutateLecture.mutateAsync({
        name: value.name.trim(),
        complete: value.status === 'completed',
        lecture: props.lecture
      });
      setOpenDialog(false);
    }
  });

  const selectOptions = [
    { value: 'active', label: 'Active' },
    { value: 'completed', label: 'Completed' }
  ];

  return (
    <Dialog open={openDialog} onOpenChange={setOpenDialog}>
      <Tooltip>
        <DialogTrigger render={<TooltipTrigger />}>
          <Pencil className={'size-5 fill-primary text-card!'} />
        </DialogTrigger>
        <TooltipContent>
          <p>Edit course</p>
        </TooltipContent>
      </Tooltip>
      <DialogContent className="sm:max-w-186">
        <DialogHeader className={'p-6 border-b'}>
          <DialogTitle>Edit course</DialogTitle>
        </DialogHeader>
        <form
          id={'edit-lecture-form'}
          onSubmit={event => {
            event.preventDefault();
            form.handleSubmit();
          }}
        >
          <FieldGroup className={'p-6 gap-4'}>
            <form.Field
              name="name"
              validators={{
                onChange: ({ value }) => {
                  if (value.length > 255) {
                    return 'Name is too long.';
                  } else if (value.trim().length === 0) {
                    return 'Name is empty.';
                  }
                  return undefined;
                }
              }}
              children={field => (
                <Field data-invalid={!field.state.meta.isValid}>
                  <Label htmlFor={field.name}>Name*</Label>
                  <Input
                    id={field.name}
                    name={field.name}
                    value={field.state.value}
                    required={true}
                    aria-invalid={!field.state.meta.isValid}
                    onChange={e => field.handleChange(e.target.value)}
                  ></Input>
                  {!field.state.meta.isValid && (
                    <em role={'alertdialog'} className={'text-red-700'}>
                      {field.state.meta.errors.join(', ')}
                    </em>
                  )}
                </Field>
              )}
            ></form.Field>
            <form.Field
              name={'status'}
              children={field => (
                <Field id={'select-field'}>
                  <Label htmlFor={field.name}>Status</Label>
                  <Select
                    name={field.name}
                    items={selectOptions}
                    onValueChange={value => field.handleChange(value as string)}
                  >
                    <SelectTrigger className={'bg-white'}>
                      <SelectValue
                        placeholder={
                          field.state.value === 'active'
                            ? 'Active'
                            : 'Completed'
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
          </FieldGroup>
        </form>
        <DialogFooter>
          <Button type={'submit'} form={'edit-lecture-form'}>
            Save
          </Button>
          <Button variant={'outline'} onClick={() => setOpenDialog(false)}>
            Cancel
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
