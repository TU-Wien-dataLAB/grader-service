import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger
} from '../../../shadcn-components/ui/dropdown-menu';
import { EllipsisVertical } from 'lucide-react';
import React, { useState } from 'react';
import { AssignmentDetail } from '../../../../model/assignmentDetail';
import { ReleaseDialog } from './release-dialog';
import { useParams } from 'react-router';
import { DeleteDialog } from './delete-dialog';
import { useAssignmentStatus } from '../../../hooks/assignment/assignment-status-hook';
import { AssignmentSettingsDialog } from './assignment-settings-dialog';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger
} from '../../../shadcn-components/ui/tooltip';
import { CompleteDialog } from './complete-dialog';

interface IAssignmentActions {
  assignment: AssignmentDetail;
}

export const AssignmentActions = (props: IAssignmentActions) => {
  const { handleRelease, handleUnrelease } = useAssignmentStatus();
  const params = useParams();
  const lectureId = Number(params.id);
  const [openReleaseDialog, setOpenReleaseDialog] = useState(false);
  const [openDeleteDialog, setOpenDeleteDialog] = useState(false);
  const [openSettingsDialog, setOpenSettingsDialog] = useState(false);
  const [openCompleteDialog, setOpenCompleteDialog] = useState(false);

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
          <DropdownMenuItem onClick={() => setOpenSettingsDialog(true)}>
            Edit
          </DropdownMenuItem>
          <DropdownMenuItem
            hidden={props.assignment.status !== 'created'}
            onClick={() => setOpenReleaseDialog(true)}
          >
            Release
          </DropdownMenuItem>
          <DropdownMenuItem
            hidden={
              props.assignment.status === 'created' ||
              props.assignment.status === 'pushed'
            }
            disabled={props.assignment.status !== 'released'}
            onClick={() => handleUnrelease(props.assignment, lectureId)}
          >
            Undo release
          </DropdownMenuItem>
          <DropdownMenuItem
            hidden={props.assignment.status === 'complete'}
            disabled={props.assignment.status !== 'released'}
            onClick={() => setOpenCompleteDialog(true)}
          >
            Complete
          </DropdownMenuItem>
          <DropdownMenuItem
            hidden={props.assignment.status !== 'complete'}
            onClick={() => handleRelease(props.assignment, lectureId)}
          >
            Undo Complete
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => setOpenDeleteDialog(true)}>
            Delete
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
      {openReleaseDialog && (
        <ReleaseDialog
          assignments={props.assignment}
          lectureId={lectureId}
          openDialog={openReleaseDialog}
          setOpenDialog={setOpenReleaseDialog}
        />
      )}
      {openDeleteDialog && (
        <DeleteDialog
          assignment={props.assignment}
          lectureId={lectureId}
          openDialog={openDeleteDialog}
          setOpenDialog={setOpenDeleteDialog}
        />
      )}
      {openSettingsDialog && (
        <AssignmentSettingsDialog
          assignment={props.assignment}
          lectureId={lectureId}
          openDialog={openSettingsDialog}
          setOpenDialog={setOpenSettingsDialog}
        />
      )}
      {openCompleteDialog && (
        <CompleteDialog
          assignment={props.assignment}
          lectureId={lectureId}
          openDialog={openCompleteDialog}
          setOpenDialog={setOpenCompleteDialog}
        />
      )}
    </>
  );
};
