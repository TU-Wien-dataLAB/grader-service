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
import { SUBMISSION_FILTER_OPTIONS } from './export-submissions';

interface ISynchronizeGradesWithLTIProps {
  openDialog: boolean;
  setOpenDialog: React.Dispatch<React.SetStateAction<boolean>>;
}

export const SynchronizeGradesWithLTIDialog = (
  props: ISynchronizeGradesWithLTIProps
) => {
  const params = useParams();
  const lectureId = Number(params.lid);
  const assignmentId = Number(params.aid);
  const { setStatus } = useMutationStatus();
  const [filterValue, setFilterValue] = useState<'latest' | 'best'>('best');

  const synchronizeMutation = useMutation({
    mutationFn: async () => {
      return await ltiSyncSubmissions(lectureId, assignmentId, filterValue);
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
    synchronizeMutation.mutate();
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
              value={filterValue}
              items={SUBMISSION_FILTER_OPTIONS}
              onValueChange={value =>
                setFilterValue(value as 'latest' | 'best')
              }
            >
              <SelectTrigger
                aria-placeholder="Choose an option"
                className={`bg-white ${!filterValue && 'border border-[#DC182C]'}`}
              >
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  {SUBMISSION_FILTER_OPTIONS.map(option => (
                    <SelectItem key={option.value} value={option.value}>
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
