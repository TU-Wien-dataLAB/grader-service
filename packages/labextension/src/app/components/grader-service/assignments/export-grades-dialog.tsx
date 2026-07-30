import React from 'react';
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle
} from '../../../shadcn-components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '../../../shadcn-components/ui/select';
import { Button } from '../../../shadcn-components/ui/button';
import { exportGrades } from '../../../../services/lectures.service';
import { lectureBasePath, openFile } from '../../../../services/file.service';
import { Lecture } from '../../../../model/lecture';
import { enqueueSnackbar } from 'notistack';
import { goToPath } from '../../../../services/file-browser.service';
import { Separator } from '../../../shadcn-components/ui/separator';

interface IExportGradesDialogProps {
  lecture: Lecture;
  isOpen: boolean;
  setIsOpen: (isOpen: boolean) => void;
}

export const ExportGradesDialog = (props: IExportGradesDialogProps) => {
  const [format, setFormat] = React.useState<'csv' | 'json'>('csv');
  const [filter, setFilter] = React.useState<'best' | 'latest'>('best');

  const handleExport = async () => {
    try {
      await exportGrades(props.lecture.id, filter, format);
      // open file in new tab
      await openFile(
        `${lectureBasePath}${props.lecture.code}/${props.lecture.name}_${filter}_submissions.${format}`
      );
      // go into correct directory
      await goToPath(`${lectureBasePath}${props.lecture.code}`);
    } catch (error: any) {
      console.error('Error exporting grades:', error);
      enqueueSnackbar(error.message || 'Failed to export grades', {
        variant: 'error'
      });
    } finally {
      props.setIsOpen(false);
    }
  };

  const FORMAT_OPTIONS = [
    { label: 'CSV', value: 'csv' },
    { label: 'JSON', value: 'json' }
  ];
  const FILTER_OPTIONS = [
    { label: 'Best submissions', value: 'best' },
    { label: 'Latest submissions', value: 'latest' }
  ];
  return (
    <Dialog open={props.isOpen} onOpenChange={props.setIsOpen}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Export assignments</DialogTitle>
        </DialogHeader>
        <div
          className={
            'flex flex-col gap-4 p-6 items-start self-stretch border-t border-border'
          }
        >
          <Select
            value={format}
            onValueChange={setFormat}
            items={FORMAT_OPTIONS}
          >
            <SelectTrigger className={'w-full'}>
              <SelectValue placeholder="Select a format" />
            </SelectTrigger>
            <SelectContent>
              {FORMAT_OPTIONS.map(({ label, value }) => (
                <SelectItem key={value} value={value}>
                  {label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select
            value={filter}
            onValueChange={setFilter}
            items={FILTER_OPTIONS}
          >
            <SelectTrigger className={'w-full'}>
              <SelectValue placeholder="Select an option" />
            </SelectTrigger>
            <SelectContent>
              {FILTER_OPTIONS.map(({ label, value }) => (
                <SelectItem key={value} value={value}>
                  {label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <DialogFooter>
          <Button onClick={handleExport}>Export</Button>
          <DialogClose render={<Button variant="outline">Cancel</Button>} />
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
