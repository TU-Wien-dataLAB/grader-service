import React, { useMemo } from 'react';
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
import { FieldGroup } from '../../../shadcn-components/ui/field';
import { Input } from '../../../shadcn-components/ui/input';
import { Label } from '../../../shadcn-components/ui/label';
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
  SelectLabel
} from '../../../shadcn-components/ui/select';
import { GlobalObjects } from '../../../../index';
import { Separator } from '../../../shadcn-components/ui/separator';
import { PathExt } from '@jupyterlab/coreutils';
import { useForm } from '@tanstack/react-form';
import { Kernel } from '@jupyterlab/services';
import {
  getFiles,
  lectureBasePath
} from '../../../../services/local-file.service';
import { useQuery } from '@tanstack/react-query';

type KernelSelection =
  | { mode: 'none' }
  | { mode: 'spec'; kernelName: string }
  | { mode: 'existing'; kernelId: string };

interface IKernelOption {
  value: string;
  label: string;
  selection: KernelSelection;
}

interface INewNotebookDialogProps {
  lectureCode: string;
  assignmentId: number;
}

export const NewNotebookDialog = (props: INewNotebookDialogProps) => {
  const kernelSpecs = GlobalObjects.serviceManager.kernelspecs.specs;
  const noKernel: IKernelOption = {
    value: 'none',
    label: 'No Kernel',
    selection: { mode: 'none' }
  };
  const getAvailableKernels = (): IKernelOption[] => {
    if (!kernelSpecs) {
      return [];
    }

    return Object.entries(kernelSpecs.kernelspecs).map(([name, spec]) => ({
      value: name,
      label: spec?.display_name ?? name,
      selection: { mode: 'spec', kernelName: name }
    }));
  };

  const getExistingSessions = (): IKernelOption[] => {
    const running = GlobalObjects.serviceManager.sessions.running();
    if (!running) {
      return [];
    }
    return Array.from(running)
      .filter(s => s.type === 'notebook' && s.kernel?.id)
      .map(s => ({
        value: `existing:${s.kernel!.id}`,
        label: PathExt.basename(s.path),
        selection: { mode: 'existing', kernelId: s.kernel!.id }
      }));
  };

  const availableKernels = getAvailableKernels();
  const existingKernels = getExistingSessions();
  const items = [noKernel, ...availableKernels, ...existingKernels];

  const [dialogOpen, setDialogOpen] = React.useState(false);

  const srcPath = useMemo(
    () => `${lectureBasePath}${props.lectureCode}/source/${props.assignmentId}`,
    [props.lectureCode, props.assignmentId]
  );
  const { data: files = [] } = useQuery({
    queryKey: ['files', props.lectureCode, props.assignmentId, 'source'],
    queryFn: async () => {
      return await getFiles(srcPath);
    }
  });

  const notebookExists = (notebookName: string): boolean => {
    return files.some(file => file.name === notebookName);
  };

  const createNamedNotebook = async (
    notebookName: string,
    kernel: IKernelOption
  ) => {
    // retrieve path of the current directory
    const directory =
      GlobalObjects.browserFactory.tracker.currentWidget.model.path;
    // if the .ipynb extension is not present, add it
    if (!notebookName.endsWith('.ipynb')) {
      notebookName += '.ipynb';
    }
    const path = directory ? `${directory}/${notebookName}` : notebookName;

    const metadata: Record<string, any> = {};
    if (kernel.selection.mode === 'spec') {
      const spec = kernelSpecs?.kernelspecs[kernel.selection.kernelName];
      metadata.kernelspec = {
        name: kernel.selection.kernelName,
        display_name: spec?.display_name ?? kernel.selection.kernelName,
        language: spec?.language ?? ''
      };
    }
    // mode 'none' and 'existing' both leave kernelspec metadata unset —
    // 'existing' will pick up the connected kernel's info once attached
    const contents = GlobalObjects.serviceManager.contents;
    const model = await contents.save(path, {
      type: 'notebook',
      content: {
        cells: [],
        metadata,
        nbformat: 4,
        nbformat_minor: 5
      }
    });

    let kernelPreference: Partial<Kernel.IModel> | undefined;
    switch (kernel.selection.mode) {
      case 'none':
        kernelPreference = null;
        break;
      case 'spec':
        kernelPreference = { name: kernel.selection.kernelName };
        break;
      case 'existing':
        kernelPreference = { id: kernel.selection.kernelId };
        break;
    }

    return GlobalObjects.docManager.open(
      model.path,
      'notebook',
      kernelPreference
    );
  };

  const form = useForm({
    defaultValues: {
      notebookName: 'Untitled.ipynb',
      kernel: noKernel
    },
    onSubmit: async ({ value }) => {
      await createNamedNotebook(value.notebookName, value.kernel);
      setDialogOpen(false);
      form.reset();
    }
  });
  return (
    <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
      <DialogTrigger
        render={
          <Button variant={'outline'} className={'ml-auto'}>
            New notebook
          </Button>
        }
      />
      <form
        id={'new-notebook-form'}
        onSubmit={e => {
          e.preventDefault();
          form.handleSubmit();
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>New notebook</DialogTitle>
          </DialogHeader>
          <Separator />
          <FieldGroup className={'p-6 gap-4'}>
            <form.Field
              name={'notebookName'}
              children={field => (
                <>
                  <Label htmlFor={'notebook-name'}>Name*</Label>
                  <Input
                    id={'notebook-name'}
                    type={'text'}
                    value={field.state.value}
                    onChange={e => field.handleChange(e.target.value)}
                    required
                    aria-invalid={!field.state.meta.isValid}
                  />
                  {!field.state.meta.isValid && (
                    <em role="alert" className={'text-red-700'}>
                      {field.state.meta.errors.join(', ')}
                    </em>
                  )}
                </>
              )}
              validators={{
                onChange: ({ value }) => {
                  const trimmedValue = value.trim();
                  if (trimmedValue.length > 255) {
                    return 'Name is too long.';
                  } else if (trimmedValue.length === 0) {
                    return 'Name is empty.';
                  } else if (notebookExists(trimmedValue)) {
                    return 'Notebook already exists.';
                  }
                  return undefined;
                }
              }}
            ></form.Field>
            <form.Field
              name={'kernel'}
              children={field => (
                <>
                  <Label htmlFor={'kernel'}>Kernel</Label>
                  <Select
                    items={items}
                    value={field.state.value.value}
                    onValueChange={val => {
                      const option = items.find(i => i.value === val);
                      if (option) {
                        field.handleChange(option);
                      }
                    }}
                  >
                    <SelectTrigger id={'kernel'} className={'w-full'}>
                      <SelectValue placeholder="Select a kernel" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectGroup>
                        <SelectItem key={noKernel.value} value={noKernel.value}>
                          {noKernel.label}
                        </SelectItem>
                      </SelectGroup>
                      {availableKernels.length > 0 && (
                        <SelectGroup>
                          <SelectLabel>Start Kernel</SelectLabel>
                          {availableKernels.map(item => (
                            <SelectItem key={item.value} value={item.value}>
                              {item.label}
                            </SelectItem>
                          ))}
                        </SelectGroup>
                      )}
                      {existingKernels.length > 0 && (
                        <SelectGroup>
                          <SelectLabel>Connect to existing Kernel</SelectLabel>
                          {existingKernels.map(item => (
                            <SelectItem key={item.value} value={item.value}>
                              {item.label}
                            </SelectItem>
                          ))}
                        </SelectGroup>
                      )}
                    </SelectContent>
                  </Select>
                </>
              )}
            ></form.Field>
          </FieldGroup>
          <DialogFooter>
            <Button
              type={'submit'}
              form={'new-notebook-form'}
              disabled={!form.state.isValid}
            >
              Create notebook
            </Button>
            <DialogClose render={<Button variant="outline">Cancel</Button>} />
          </DialogFooter>
        </DialogContent>
      </form>
    </Dialog>
  );
};
