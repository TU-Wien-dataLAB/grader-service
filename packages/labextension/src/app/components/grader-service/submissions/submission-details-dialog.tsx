import React from 'react';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle
} from '../../../shadcn-components/ui/sheet';
import { Submission } from '../../../../model/submission';
import { Separator } from '../../../shadcn-components/ui/separator';
import { EditedBadge } from '../../ui/badges';
import SubmissionDetailInfo from './submission-detail-info';
import SubmissionFiles from './submission-files';
import { Button } from '../../../shadcn-components/ui/button';
import { useNavigate, useParams } from 'react-router';

type SubmissionDetailsDialogProps = {
  submission: Submission | null;
  onClose: () => void;
};

export type SubmissionFile = {
  id: string;
  name: string;
  score?: number;
  maxScore?: number;
  manuallyGraded?: boolean;
};

export type SubmissionFolder = {
  id: string;
  name: string;
  files: Array<SubmissionFile>;
};

export const SubmissionDetailsDialog = ({
  submission,
  onClose
}: SubmissionDetailsDialogProps) => {
  const params = useParams();

  const lectureId = Number(params.lid);
  const assignmentId = Number(params.aid);
  const navigate = useNavigate();

  const goToEditSubmission = () => {
    navigate(
      `/lectures/${lectureId}/assignments/${assignmentId}/submissions/${submission.id}/edit`
    );
  };

  return (
    <Sheet open={submission !== null} onOpenChange={open => !open && onClose()}>
      <SheetContent
        side="right"
        className="gap-0 overflow-y-auto bg-[#F5F5F5] pb-6 absolute"
        style={{ width: '40vw', maxWidth: '100vw' }}
      >
        {submission && (
          <>
            <SheetHeader className="px-6 py-6">
              <SheetTitle className="text-2xl font-bold flex gap-4">
                <h3>Submission details</h3>
                <EditedBadge />
              </SheetTitle>
            </SheetHeader>
            <Separator />

            <div className="px-6 text-base">
              <SubmissionDetailInfo submission={submission} />
              <div className="py-6">
                <div className="flex justify-between mb-2">
                  <h3 className="text-xl font-bold mb-2">Submission</h3>
                  <Button variant="outline">Autograde</Button>
                </div>
                <div>
                  <SubmissionFiles files={null} />
                  <div className="flex flex-start gap-4 mt-4">
                    <Button variant="default">Generate feedback</Button>
                    <Button variant="outline" onClick={goToEditSubmission}>
                      Edit submission
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </>
        )}
      </SheetContent>
    </Sheet>
  );
};
