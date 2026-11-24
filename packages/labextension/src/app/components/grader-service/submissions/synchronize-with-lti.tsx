import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle
} from '../../../shadcn-components/ui/dialog';
import { Button } from '../../../shadcn-components/ui/button';
import { useMutation } from '@tanstack/react-query';
import { ltiSyncSubmissions } from '../../../../services/submissions.service';
import { useParams } from 'react-router';
import { queryClient, useMutationStatus } from '../../../../widget';
import { Field } from '../../../shadcn-components/ui/field';
import { Label } from '../../../shadcn-components/ui/label';
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '../../../shadcn-components/ui/select';
import { RowSelectionState } from '@tanstack/react-table';

interface ISynchronizeGradesWithLTIProps {
  openDialog: boolean;
  setOpenDialog: React.Dispatch<React.SetStateAction<boolean>>;
  selectedSubmissions: RowSelectionState;
}
export const SUBMISSION_SYNC_LTI_FILTER_OPTIONS = [
  { value: 'best', label: 'Best submissions' },
  { value: 'latest', label: 'Latest submissions' },
  { value: 'selection', label: 'Selected submissions' }
] as const;

export const SynchronizeGradesWithLTIDialog = (
  props: ISynchronizeGradesWithLTIProps
) => {
  const params = useParams();
  const lectureId = Number(params.lid);
  const assignmentId = Number(params.aid);
  const { setStatus } = useMutationStatus();
  const [filter, setFilter] = useState<'latest' | 'best' | 'selection'>('best');
  const hasSelection = Object.values(props.selectedSubmissions).some(Boolean);

  const synchronizeMutation = useMutation({
    mutationFn: async ({
      option,
      selected
    }: {
      option: string;
      selected?: number[];
    }) => {
      return await ltiSyncSubmissions(
        lectureId,
        assignmentId,
        option,
        selected
      );
    },
    onSuccess: response => {
      const syncedPlatforms = response.synced_platforms;
      if (!syncedPlatforms.length) {
        setStatus({
          message:
            'No connected learning platform was available for grade sync',
          status: 'error'
        });
        return;
      }
      syncedPlatforms.forEach(platformResult => {
        setStatus({
          message: `${platformResult.platform}: Synced ${platformResult.synced_user}/${platformResult.syncable_users} users`,
          status: 'success'
        });
      });
      props.setOpenDialog(false);
      queryClient.invalidateQueries({ queryKey: ['submissions'] });
    },
    onError: () => {
      setStatus({
        message: 'Something went wrong. Please, try again!',
        status: 'error'
      });
    }
  });

  const handleSynchronize = () => {
    if (filter === 'selection') {
      synchronizeMutation.mutate({
        option: filter,
        selected: Object.keys(props.selectedSubmissions).map(Number)
      });
    } else {
      synchronizeMutation.mutate({ option: filter });
    }
    props.setOpenDialog(false);
  };

  return (
    <Dialog open={props.openDialog} onOpenChange={props.setOpenDialog}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Synchronize grades with LTI</DialogTitle>
        </DialogHeader>
        <div className="p-6">
          <Field id={'select-field'}>
            <Label className="font-bold" htmlFor="filter">
              Filter *
            </Label>
            <Select
              name="filter"
              value={filter}
              items={SUBMISSION_SYNC_LTI_FILTER_OPTIONS}
              onValueChange={value =>
                setFilter(value as 'latest' | 'best' | 'selection')
              }
            >
              <SelectTrigger
                aria-placeholder="Choose an option"
                className={`bg-white ${!filter && 'border border-[#DC182C]'}`}
              >
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  {SUBMISSION_SYNC_LTI_FILTER_OPTIONS.map(option => (
                    <SelectItem
                      disabled={option.value === 'selection' && !hasSelection}
                      key={option.value}
                      value={option.value}
                    >
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectGroup>
              </SelectContent>
            </Select>
          </Field>
        </div>
        <DialogFooter>
          <Button
            type={'button'}
            variant="default"
            interactive={false}
            onClick={handleSynchronize}
          >
            Synchronize
          </Button>
          <Button
            type={'button'}
            variant={'outline'}
            onClick={() => props.setOpenDialog(false)}
            autoFocus
          >
            Cancel
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
