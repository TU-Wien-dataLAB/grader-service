import React, { useState } from 'react';
import { Submission } from '../../../../model/submission';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '../../../shadcn-components/ui/select';
import { formatSubmittedAt } from './utils';
import { CustomBadge } from '../../ui/badges';
import { AutoStatus } from '../../../../model/autoStatus';
import { Assignment } from '../../../../model/assignment';

enum feedback {
  generated = 'Feedback given',
  not_generated = 'No Feedback',
  generation_failed = 'Feedback failed',
  generating = 'Feedback pending',
  feedback_outdated = 'Feedback outdated'
}

const SCORE_OPTIONS = Array.from({ length: 11 }, (_, i) => {
  const value = i / 10;
  return { label: value.toFixed(1), value };
});

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
  assignment: Assignment;
}

const SubmissionDetailInfo = ({
  submission,
  isEditMode = false,
  assignment
}: ISubmissionDetailInfoProps) => {
  const [scoreScaling, setScoreScaling] = useState<number | null>(
    submission.score_scaling
  );

  return (
    <div className="py-6">
      <h3 className="text-xl font-bold mb-2">Details</h3>
      <dl className="flex flex-col flex-start gap-3">
        <DetailRow label="Assignment">{assignment?.name}</DetailRow>
        <DetailRow label="Name">
          {submission?.user_display_name ?? '—'}
        </DetailRow>
        <DetailRow label="Grading method">
          <CustomBadge type={submission.auto_status as AutoStatus} />
        </DetailRow>
        <DetailRow label="Feedback">
          {feedback[submission.feedback_status]}
        </DetailRow>
        <DetailRow label="Submitted at">
          {formatSubmittedAt(submission?.submitted_at)}
        </DetailRow>
        <DetailRow label="Achieved points">
          {(submission?.grading_score ?? 0).toFixed(2)}/5
        </DetailRow>
        <DetailRow label="Extra credit"> ? </DetailRow>
        <DetailRow label="Final score">{submission.score ?? '—'}</DetailRow>
        {!isEditMode && (
          <DetailRow label="Score scaling">
            <Select
              value={scoreScaling}
              onValueChange={opt => setScoreScaling(opt)}
            >
              <SelectTrigger className="w-64 rounded-none border-[#b5b5b5] bg-white">
                <SelectValue placeholder="Choose option" />
              </SelectTrigger>
              <SelectContent>
                {SCORE_OPTIONS.map(option => (
                  <SelectItem key={option.value} value={option.value}>
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
