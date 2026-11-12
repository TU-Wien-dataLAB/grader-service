import React from 'react';
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from '../../../shadcn-components/ui/card';
import { Button } from '../../../shadcn-components/ui/button';
import { Octagon, OctagonAlert } from 'lucide-react';
import { getDateTime } from '../../utils/utils';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger
} from '../../../shadcn-components/ui/tooltip';
import { Assignment } from '../../../../model/assignment';
import { Link } from 'react-router';
import { useParams } from 'react-router';
import { getSubmissionCount, getSubmissions } from '../../../../services/submissions.service';
import { useQuery } from '@tanstack/react-query';
import { ChangesAssignmentBadge, FeedbackAssignmentBadge, NewAssignmentBadge, NoSubmissionAssignmentBadge } from '../../ui/badges';
import { MoreTimeIcon } from '../../../../assets/more-time-icon';
import { getFiles, lectureBasePath } from '../../../../services/local-file.service';
import { lectureQuery } from '../../../../services/queries/lectures.queries';

export interface IAssignment {
  key: React.Key;
  assignment: Assignment;
}

export const AssignmentCardStudent = (props: IAssignment) => {
    const params = useParams();
    const lectureId = Number(params.id);

    const { data: submissionCount = 0 } = useQuery({
    queryKey: ['submissionCount', lectureId, props.assignment.id],
    queryFn: async () => {
        const res = await getSubmissionCount(lectureId, props.assignment.id);
        return res.submission_count;
    },
    });

    const { data: feedbackStatus } = useQuery({
    queryKey: ['feedbackStatus', lectureId, props.assignment.id],
    queryFn: async () => {
        const submissions = await getSubmissions(lectureId, props.assignment.id, undefined, false);
        for (const s of submissions){
            if(s.feedback_status) return true;
        }
        return false;
    },
    }); 

    const { data: lecture } = useQuery(
      lectureQuery(lectureId)
    );

    const { data: isAssignmentfetched } = useQuery({
    queryKey: ['filesStatus', lectureId, props.assignment.id],
    queryFn: async () => {
        const files = await getFiles(`${lectureBasePath}${lecture?.code}/assignments/${props.assignment.id}`);
        return files?.length > 0;
    },
    }); 

    const badgeCase = () => {
        const deadline = props.assignment.settings?.deadline
        if (deadline && (new Date(deadline) < new Date()) && submissionCount === 0) {
            return <NoSubmissionAssignmentBadge/>;
        } 
        else if (!isAssignmentfetched) {
            return <NewAssignmentBadge/>;
        } else if (false) {
            return <ChangesAssignmentBadge/>;
        }else if (feedbackStatus) {
            return <FeedbackAssignmentBadge/>;
        }
    }

  return  (
      <Card
        className={`flex self-stretch gap-0 row-span-1 col-span-1 p-0`}
      >
        <CardHeader
          className={`p-4 flex flex-col items-center}`}
        >
          <CardTitle className={'text-[18px] line-clamp-2'}>
            {props.assignment.name}
          </CardTitle>
          {badgeCase()}
        </CardHeader>
        <CardContent
          className={`flex flex-col gap-4 px-4`}
        >
          <div
            className={`grid grid-cols-2 gap-4`}
          >
            <div className={'flex flex-col items-start gap-2'}>
              <h6 className={'text-sm font-medium'}>Deadline</h6>
              <div className={'flex flex-row gap-2 items-center'}>
                {props.assignment.settings?.deadline
                  ? getDateTime(new Date(props.assignment.settings?.deadline))
                  : '-'}
                {props.assignment.settings?.deadline &&
                  new Date(props.assignment.settings?.deadline) < new Date() && (
                    <Tooltip>
                      <TooltipTrigger>
                            <span className="relative inline-flex size-4">
                            <Octagon className="absolute inset-0 size-4 fill-red-500 text-red-500" />
                            <OctagonAlert className="absolute inset-0 size-4 text-card [&>path:last-child]:stroke-red-500" />
                            </span>                      
                        </TooltipTrigger>
                      <TooltipContent>Deadline over</TooltipContent>
                    </Tooltip>
                  )}
                {props.assignment.settings?.late_submission && (new Date(props.assignment.settings?.deadline) > new Date()) &&
                    <MoreTimeIcon className="relative right-0 top-0 size-4 text-primary"/>
                }
              </div>
            </div>
            <div className={'flex flex-col gap-2 items-start'}>
                <h6 className={'text-sm font-medium'}>Submissions</h6>
                <h6>
                    {props.assignment.settings?.max_submissions
                    ? `${submissionCount}/${props.assignment.settings.max_submissions}`
                    : 'Unlimited'}                
                </h6>
            </div>
          </div>
        </CardContent>
        <CardFooter
          className={
            'items-start flex-col justify-end gap-4 self-stretch p-4'
          }
        >
            <Link to={`/student/lectures/${lectureId}/assignments/${props.assignment.id}`} className="block w-full">
                <Button className={'w-full cursor-pointer'}>
                    Go to assignment
                </Button>
            </Link>
        </CardFooter>
      </Card>
  );
};
