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

type TProps = {
  setShowNewSubmissionForm: (val: boolean) => void;
};

export const SubmissionsActions = (props: TProps) => {
  const [openExportSubmissionDialog, setOpenExportSubmissionDialog] =
    useState(false);
  const [openSynchronizeGradesDialog, setOpenSynchronizeGradesDialog] =
    useState(false);

  console.log(openExportSubmissionDialog, openSynchronizeGradesDialog);

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
          <DropdownMenuItem
            onClick={() => props.setShowNewSubmissionForm(true)}
          >
            New submission
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => setOpenExportSubmissionDialog(true)}>
            Export submissions
          </DropdownMenuItem>

          <DropdownMenuItem
            onClick={() => setOpenSynchronizeGradesDialog(true)}
          >
            Synchronize grades with Moodle
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </>
  );
};
