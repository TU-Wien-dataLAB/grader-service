import React from 'react';
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger
} from '../../../shadcn-components/ui/dialog';
import { Button } from '../../../shadcn-components/ui/button';
import { Field, FieldGroup } from '../../../shadcn-components/ui/field';
import { Input } from '../../../shadcn-components/ui/input';
import { Label } from '../../../shadcn-components/ui/label';
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '../../../shadcn-components/ui/select';
import { GlobalObjects } from '../../../../index';
import { Separator } from '../../../shadcn-components/ui/separator';

export const NewNotebookDialog = () => {
  const getAvailableKernels = () => {
    const specs = GlobalObjects.serviceManager.kernelspecs.specs;
    if (!specs) {
      return [];
    }

    return Object.entries(specs.kernelspecs).map(([name, spec]) => ({
      value: name,
      label: spec?.display_name ?? name
    }));
  };

  const items = getAvailableKernels();

  //TODO: find a way to set a name for notebook and then create it
  //TODO: wrap fields with form
  return (
    <Dialog>
      <DialogTrigger
        render={<Button variant={'outline'}>New notebook</Button>}
      />
      <DialogContent>
        <DialogHeader>
          <DialogTitle>New notebook</DialogTitle>
        </DialogHeader>
        <Separator />
        <FieldGroup className={'p-6 gap-4'}>
          <Field>
            <Label htmlFor={'notebook-name'}>Name*</Label>
            <Input
              id={'notebook-name'}
              type={'text'}
              defaultValue={'Untitled'}
            />
          </Field>
          <Field>
            <Label htmlFor={'kernel'}>Kernel</Label>
            <Select items={items}>
              <SelectTrigger>
                <SelectValue placeholder="Select a kernel" />
              </SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  {items.map(item => (
                    <SelectItem key={item.value} value={item.value}>
                      {item.label}
                    </SelectItem>
                  ))}
                </SelectGroup>
              </SelectContent>
            </Select>
          </Field>
        </FieldGroup>
        <DialogFooter>
          <Button type={'submit'}>Create notebook</Button>
          <DialogClose render={<Button variant="outline">Cancel</Button>} />
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
