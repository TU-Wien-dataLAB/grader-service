import React from 'react';
import { AssignmentDetail } from '../../../../model/assignmentDetail';
import { useDrag } from 'react-dnd';
import {
  Card,
  CardAction,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
  ItemTypes
} from '../../../shadcn-components/ui/card';
import { Checkbox } from '../../../shadcn-components/ui/checkbox';
import { Button } from '../../../shadcn-components/ui/button';
import { OctagonAlert } from 'lucide-react';
import { getDate } from '../../utils/utils';
import { AssignmentActions } from './assignment-actions';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger
} from '../../../shadcn-components/ui/tooltip';
import { assignmentStatus, gradingType } from '../../utils/assignment-metadata';
import { useNavigate, useParams } from 'react-router';

export interface IAssignment {
  key: React.Key;
  assignment: AssignmentDetail;
  checked: boolean;
  handleChange: (checked: boolean) => void;
}

export const AssignmentCard = (props: IAssignment) => {
  const [{ isDragging }, drag, dragPreview] = useDrag(() => ({
    type: ItemTypes.CARD,
    item: {
      assignmentId: props.assignment.id,
      group: props.assignment.settings.group
    },
    collect: monitor => ({
      isDragging: monitor.isDragging()
    })
  }));
  const params = useParams();

  const lectureId = Number(params.id);
  /* assignment tabs */
  const navigate = useNavigate();
  const goToAssignment = (tab: string) => {
    navigate(`/lectures/${lectureId}/assignments/${props.assignment.id}`, {
      state: { activeTab: tab }
    });
  };

  return isDragging ? (
    <div
      ref={node => {
        dragPreview(node);
      }}
      className={`bg-[#EBEBEB] h-80 border-2 cursor-grabbing border-muted-foreground border-dashed`}
    ></div>
  ) : (
    <div
      ref={node => {
        drag(node);
      }}
      className={'cursor-grab'}
    >
      <Card
        className={`flex self-stretch gap-0 row-span-1 col-span-1 p-0 ${
          props.checked ? 'border border-primary' : ''
        }`}
      >
        <CardHeader
          className={`p-4 flex gap-4 items-center ${
            props.checked && 'bg-[#E0E7EB]'
          } ${props.assignment.status === 'complete' ? 'text-border' : ''}`}
        >
          <Checkbox
            checked={props.checked}
            disabled={props.assignment.status !== 'created'}
            onCheckedChange={() => props.handleChange(!props.checked)}
          ></Checkbox>
          <CardTitle className={'text-2xl line-clamp-2'}>
            {props.assignment.name}
          </CardTitle>
          <CardAction className={'ml-auto gap-3'}>
            <AssignmentActions assignment={props.assignment} />
          </CardAction>
        </CardHeader>
        <CardContent
          className={`flex flex-col gap-4 p-4 pt-0 ${
            props.checked && 'bg-[#E0E7EB]'
          }`}
        >
          <div className={'flex items-start gap-4'}>
            {assignmentStatus(props.assignment.status)}
            {gradingType(
              props.assignment.settings.autograde_type,
              props.assignment.status === 'complete'
            )}
          </div>
          <div
            className={`grid grid-cols-3 ${
              props.assignment.status === 'complete' ? 'text-border' : ''
            }`}
          >
            <div className={'flex flex-col items-start gap-2'}>
              <h6 className={'text-sm font-medium'}>Deadline</h6>
              <div className={'flex flex-row gap-2 items-center'}>
                {props.assignment.settings?.deadline
                  ? getDate(new Date(props.assignment.settings?.deadline))
                  : '-'}
                {props.assignment.settings?.deadline &&
                  new Date(props.assignment.settings?.deadline) <
                    new Date() && (
                    <Tooltip>
                      <TooltipTrigger>
                        <OctagonAlert className={'text-red-500 size-4'} />
                      </TooltipTrigger>
                      <TooltipContent side={'left'}>
                        Deadline over
                      </TooltipContent>
                    </Tooltip>
                  )}
              </div>
            </div>
            <div className={'flex flex-col items-start gap-2'}>
              <h6 className={'text-sm font-medium'}>Points</h6>
              <h6>{props.assignment.points.toString()}</h6>
            </div>
            <div className={'flex flex-col gap-2 items-start'}>
              <h6 className={'text-sm font-medium'}>Submissions</h6>
              <h6>1/20</h6>
            </div>
          </div>
        </CardContent>
        <CardFooter
          className={
            'items-start flex-col justify-end gap-4 self-stretch bg-[#EBEBEB] dark:bg-[#2B2B2B] p-4'
          }
        >
          <Button
            className={'w-full'}
            onClick={() => goToAssignment('notebooks-and-files')}
          >
            Go to notebooks & files
          </Button>
          <Button
            className={'w-full'}
            variant={'outline'}
            onClick={() => goToAssignment('submissions')}
          >
            Go to submissions
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
};
