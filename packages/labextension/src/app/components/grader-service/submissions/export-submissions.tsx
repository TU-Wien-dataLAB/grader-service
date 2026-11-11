import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle
} from '../../../shadcn-components/ui/dialog';
import { Button } from '../../../shadcn-components/ui/button';
import { Label } from '../../../shadcn-components/ui/label';
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '../../../shadcn-components/ui/select';
import { Field } from '../../../shadcn-components/ui/field';
import { useQuery } from '@tanstack/react-query';
import { useParams } from 'react-router';
import { useMutationStatus } from '../../../../widget';
import { exportSubmissionsData } from '../../../../services/queries/submissions.query';
import { openInNewTab } from '../../../../services/local-file.service';

interface ISynchronizeGradesWithLTIProps {
  openDialog: boolean;
  setOpenDialog: React.Dispatch<React.SetStateAction<boolean>>;
}

export const SUBMISSION_FILTER_OPTIONS = [
  { value: 'best', label: 'Best submissions' },
  { value: 'latest', label: 'Latest submissions' }
] as const;

const SUBMISSION_FORMAT_OPTIONS = [
  { value: 'csv', label: 'CSV' },
  { value: 'json', label: 'JSON' }
] as const;

export const ExportSubmissionsDialog = (
  props: ISynchronizeGradesWithLTIProps
) => {
  const [filter, setFilter] = useState<'latest' | 'best'>('best');
  const [format, setFormat] = useState<'csv' | 'json'>('csv');
  const params = useParams();
  const lectureId = Number(params.lid);
  const { setStatus } = useMutationStatus();

  const { refetch: refetchExportSubmissions } = useQuery({
    ...exportSubmissionsData(lectureId, filter, format),
    enabled: false
  });

  const handleExportSubmissions = async () => {
    const result = await refetchExportSubmissions();

    if (result.isSuccess) {
      openInNewTab(result.data.file_path.replace(/^.*?instructor\/?/, ''));
      props.setOpenDialog(false);
      setStatus({
        message: 'The submissions are exported.',
        status: 'success'
      });
    } else {
      setStatus({
        message: 'Something went wrong. Please try again.',
        status: 'error'
      });
    }
  };

  return (
    <Dialog open={props.openDialog} onOpenChange={props.setOpenDialog}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Export submissions</DialogTitle>
        </DialogHeader>
        <div className="p-6 space-y-4">
          <Field id={'select-field'}>
            <Label className="font-bold" htmlFor="filter">
              Filter *
            </Label>
            <Select
              name="filter"
              value={filter}
              items={SUBMISSION_FILTER_OPTIONS}
              onValueChange={value => setFilter(value as 'latest' | 'best')}
            >
              <SelectTrigger
                aria-placeholder="Choose an option"
                className="bg-white"
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
          <Field id={'select-field'}>
            <Label className="font-bold" htmlFor="filter">
              Format *
            </Label>
            <Select
              name="filter"
              value={format}
              items={SUBMISSION_FORMAT_OPTIONS}
              onValueChange={value => setFormat(value as 'csv' | 'json')}
            >
              <SelectTrigger
                aria-placeholder="Choose an option"
                className="bg-white"
              >
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  {SUBMISSION_FORMAT_OPTIONS.map(option => (
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
            onClick={handleExportSubmissions}
          >
            Export
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
