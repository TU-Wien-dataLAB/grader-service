import React from 'react';
import { Submission } from '../../../../model/submission';
import { AutomaticallyGradedBadge, ManuallyGradedBadge } from '../../ui/badges';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '../../../shadcn-components/ui/select';
import { formatSubmittedAt } from './utils';

const getGradingMethod = (s: Submission): 'automatic' | 'manual' =>
  s.manual_status !== undefined ? 'manual' : 'automatic';

const hasFeedback = (s: Submission): boolean => s.feedback_status !== undefined;

const DetailRow = ({
  label,
  children
}: {
  label: string;
  children: React.ReactNode;
}) => (
  <div className="flex leading-[20px]">
    <dt className="font-medium text-sm text-foreground flex-1">{label}</dt>
    <dd className="flex-3 text-sm">{children}</dd>
  </div>
);

interface ISubmissionDetailInfoProps {
  submission: Submission;
  isEditMode?: boolean;
}

const SubmissionDetailInfo = ({
  submission,
  isEditMode = false
}: ISubmissionDetailInfoProps) => {
  return (
    <div className="py-6">
      <h3 className="text-xl font-bold mb-2">Details</h3>
      <dl className="flex flex-col flex-start gap-3">
        <DetailRow label="Assignment">Submission details</DetailRow>
        <DetailRow label="Name">
          {submission?.user_display_name ?? '—'}
        </DetailRow>
        <DetailRow label="Grading method">
          {getGradingMethod(submission) === 'automatic' ? (
            <AutomaticallyGradedBadge />
          ) : (
            <ManuallyGradedBadge />
          )}
        </DetailRow>
        <DetailRow label="Feedback">
          {hasFeedback(submission) ? 'Feedback given' : 'No Feedback'}
        </DetailRow>
        <DetailRow label="Submitted at">
          {formatSubmittedAt(submission?.submitted_at)}
        </DetailRow>
        <DetailRow label="Achieved points">
          {(submission?.grading_score ?? 0).toFixed(2)}/5
        </DetailRow>
        <DetailRow label="Extra credit">
          {Math.max(
            0,
            (submission.score ?? 0) - (submission.grading_score ?? 0)
          ).toFixed(2)}
        </DetailRow>
        <DetailRow label="Final score">{submission.score ?? '—'}</DetailRow>
        {!isEditMode && (
          <DetailRow label="Score scaling">
            <Select
              value={
                submission.score_scaling !== undefined
                  ? String(submission.score_scaling)
                  : undefined
              }
            >
              <SelectTrigger className="w-64 rounded-none border-[#b5b5b5] bg-white">
                <SelectValue placeholder="Choose option" />
              </SelectTrigger>
              <SelectContent>
                {[
                  { label: '1', value: 1 },
                  { label: '2', value: 2 },
                  { label: '3', value: 3 }
                ].map(option => (
                  <SelectItem key={option.value} value={String(option.value)}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </DetailRow>
        )}
      </dl>
    </div>
  );
};

export default SubmissionDetailInfo;
