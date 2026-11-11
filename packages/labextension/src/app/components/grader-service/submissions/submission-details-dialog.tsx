import React from 'react';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle
} from '../../../shadcn-components/ui/sheet';
import { Separator } from '../../../shadcn-components/ui/separator';
import { CustomBadge } from '../../ui/badges';
import SubmissionDetailInfo from './submission-detail-info';
import SubmissionFiles from './submission-files';
import { Button } from '../../../shadcn-components/ui/button';
import { useNavigate, useParams } from 'react-router';
import {
  getFiles,
  IFile,
  lectureBasePath
} from '../../../../services/local-file.service';
import { useMutation, useQuery } from '@tanstack/react-query';
import {
  getPulledSubmissionFiles,
  getSubmissionById
} from '../../../../services/queries/submissions.query';
import { lectureQuery } from '../../../../services/queries/lectures.queries';
import {
  autogradeSubmission,
  generateFeedback
} from '../../../../services/grading.service';
import { queryClient, useMutationStatus } from '../../../../widget';
import { ErrorBanner } from '../../ui/error-banner';
import { SuccessBanner } from '../../ui/success-banner';
import { assignmentQuery } from '../../../../services/queries/assignments.queries';

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
  const { status, setStatus } = useMutationStatus();
  const { data: lecture } = useQuery(lectureQuery(lectureId));
  const { data: assignment } = useQuery(
    assignmentQuery(lectureId, assignmentId)
  );

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

  const generateFeedbackMutation = useMutation({
    mutationFn: async () => {
      await generateFeedback(lectureId, assignmentId, submissionId);
    },
    onSuccess: () => {
      setStatus({
        message: 'You successfully generated a feedback!',
        status: 'success'
      });
      queryClient.invalidateQueries({
        queryKey: ['submissionById', submissionId]
      });
    },
    onError: () => {
      setStatus({
        message: 'Failed to generate a feedback. Please, try again!',
        status: 'error'
      });
    }
  });

  const autogradeMutation = useMutation({
    mutationFn: async () => {
      await autogradeSubmission(lectureId, assignmentId, submissionId);
    },
    onSuccess: () => {
      setStatus({
        message: 'You successfully autograded a submission!',
        status: 'success'
      });
      queryClient.invalidateQueries({
        queryKey: ['submissionById', submissionId]
      });
      queryClient.invalidateQueries({
        queryKey: ['submissions']
      });
    },
    onError: () => {
      setStatus({
        message: 'Failed to autograde. Please, try again!',
        status: 'error'
      });
    }
  });

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
                {submission.edited && <CustomBadge type="edited" />}
              </SheetTitle>
            </SheetHeader>
            <Separator />
            {status.status === 'success' && (
              <div className="m-6">
                <SuccessBanner message={status.message} />
              </div>
            )}
            {status.status === 'error' && (
              <div className="m-6">
                <ErrorBanner message={status.message} />
              </div>
            )}
            <div className="px-6 text-base">
              <SubmissionDetailInfo
                submission={submission}
                assignment={assignment}
              />
              <div className="py-6">
                <div className="flex justify-between mb-2">
                  <h3 className="text-xl font-bold mb-2">Submission</h3>
                  <Button
                    onClick={() => autogradeMutation.mutate()}
                    variant="outline"
                  >
                    Autograde
                  </Button>
                </div>
                <div>
                  <SubmissionFiles files={files} />
                  <div className="flex flex-start gap-4 mt-4">
                    <Button
                      disabled={
                        submission.auto_status !== 'automatically_graded'
                      }
                      onClick={() => generateFeedbackMutation.mutate()}
                      variant="default"
                    >
                      Generate feedback
                    </Button>
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
