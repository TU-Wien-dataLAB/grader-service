import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger
} from '../../../shadcn-components/ui/dropdown-menu';
import { EllipsisVertical } from 'lucide-react';
import React, { useState } from 'react';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger
} from '../../../shadcn-components/ui/tooltip';
import { SynchronizeGradesWithLTIDialog } from './synchronize-with-lti';
import { ExportSubmissionsDialog } from './export-submissions';

type TProps = {
  setOpenNewSubmission: (val: boolean) => void;
  lectureId: number;
};

export const SubmissionsActions = (props: TProps) => {
  const [openSynchronizeGradesDialog, setOpenSynchronizeGradesDialog] =
    useState(false);
  const [openExportSubmissionsDialog, setOpenExportSubmissionsDialog] =
    useState(false);

  return (
    <>
      <DropdownMenu modal={false}>
        <Tooltip>
          <TooltipTrigger render={<DropdownMenuTrigger />}>
            <EllipsisVertical className={'size-4 text-primary'} />
          </TooltipTrigger>
          <TooltipContent>
            <p>More options</p>
          </TooltipContent>
        </Tooltip>
        <DropdownMenuContent className={'rounded-xs'}>
          <DropdownMenuItem onClick={() => props.setOpenNewSubmission(true)}>
            New submission
          </DropdownMenuItem>
          <DropdownMenuItem
            onClick={() => setOpenExportSubmissionsDialog(true)}
          >
            Export submissions
          </DropdownMenuItem>

          <DropdownMenuItem
            onClick={() => setOpenSynchronizeGradesDialog(true)}
          >
            Synchronize grades with LTI
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      {openSynchronizeGradesDialog && (
        <SynchronizeGradesWithLTIDialog
          openDialog={openSynchronizeGradesDialog}
          setOpenDialog={setOpenSynchronizeGradesDialog}
        />
      )}
      {openExportSubmissionsDialog && (
        <ExportSubmissionsDialog
          openDialog={openExportSubmissionsDialog}
          setOpenDialog={setOpenExportSubmissionsDialog}
        />
      )}
    </>
  );
};
