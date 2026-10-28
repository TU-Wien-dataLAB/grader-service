import React from 'react';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle
} from '../../../shadcn-components/ui/sheet';
import { Separator } from '../../../shadcn-components/ui/separator';
import { EditedBadge } from '../../ui/badges';
import SubmissionDetailInfo from './submission-detail-info';
import SubmissionFiles from './submission-files';
import { Button } from '../../../shadcn-components/ui/button';
import { useNavigate, useParams } from 'react-router';
import {
  getFiles,
  IFile,
  lectureBasePath
} from '../../../../services/local-file.service';
import { useQuery } from '@tanstack/react-query';
import {
  getPulledSubmissionFiles,
  getSubmissionById
} from '../../../../services/queries/submissions.query';
import { lectureQuery } from '../../../../services/queries/lectures.queries';

type SubmissionDetailsDialogProps = {
  submissionId: number;
  onClose: () => void;
};

export type TSubmissionDirectory = IFile & { content: IFile };
export const SubmissionDetailsDialog = ({
  submissionId,
  onClose
}: SubmissionDetailsDialogProps) => {
  const params = useParams();

  const lectureId = Number(params.lid);
  const assignmentId = Number(params.aid);
  const navigate = useNavigate();
  const { data: lecture } = useQuery(lectureQuery(lectureId));

  const goToEditSubmission = () => {
    navigate(
      `/lectures/${lectureId}/assignments/${assignmentId}/submissions/${submissionId}/edit`
    );
  };

  const isSubmissionFilesPulled = useQuery(
    getPulledSubmissionFiles(lectureId, assignmentId, submissionId)
  );

  const path =
    lecture && assignmentId
      ? `${lectureBasePath}${lecture.code}/edit/${assignmentId}/${submissionId}`
      : null;

  const { data: files = [] } = useQuery<(IFile | TSubmissionDirectory)[]>({
    queryKey: ['submissionFiles', path, isSubmissionFilesPulled.status],
    queryFn: () => getFiles(path),
    enabled: !!path && isSubmissionFilesPulled.status === 'success'
  });

  const { data: submission } = useQuery(
    getSubmissionById(lectureId, assignmentId, submissionId)
  );

  return (
    <Sheet
      open={submissionId !== null}
      onOpenChange={open => !open && onClose()}
    >
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
                  <SubmissionFiles files={files} />
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
