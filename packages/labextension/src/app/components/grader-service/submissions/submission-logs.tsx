import React, { useMemo } from 'react';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle
} from '../../../shadcn-components/ui/sheet';
import { Separator } from '../../../shadcn-components/ui/separator';
import { useParams } from 'react-router';
import { useQuery } from '@tanstack/react-query';
import { getSubmissionLogsData } from '../../../../services/queries/submissions.query';

type SubmissionLogsDialogProps = {
  submissionId: number;
  onClose: () => void;
};

export const SubmissionLogsDialog = ({
  submissionId,
  onClose
}: SubmissionLogsDialogProps) => {
  const params = useParams();

  const lectureId = Number(params.lid);
  const assignmentId = Number(params.aid);

  const { data: submissionLogs } = useQuery(
    getSubmissionLogsData(lectureId, assignmentId, submissionId)
  );

  const TIMESTAMP_SPLIT = /(?=\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\])/;

  const lines = useMemo(
    () =>
      submissionLogs
        ?.split(TIMESTAMP_SPLIT)
        .map(l => l.trim())
        .filter(Boolean),
    [submissionLogs]
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
        <SheetHeader className="px-6 py-6">
          <SheetTitle className="text-2xl font-bold flex gap-4">
            <h3>Logs</h3>
          </SheetTitle>
        </SheetHeader>
        <Separator />
        <div className="px-4 py-2 m-6 h-full text-base bg-black overflow-auto">
          {lines ? (
            lines.map((line, i) => (
              <p
                key={i}
                className="whitespace-pre-wrap break-all text-white text-sm leading-[20px] mb-2"
              >
                {line}
              </p>
            ))
          ) : (
            <p className="text-white text-sm leading-[20px]">Logs not found.</p>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
};
