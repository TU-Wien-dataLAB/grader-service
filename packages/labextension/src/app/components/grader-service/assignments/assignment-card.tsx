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
import { AssignmentSettings } from '../../../../model/assignmentSettings';
import AutogradeTypeEnum = AssignmentSettings.AutogradeTypeEnum;
import { getDate } from '../../utils/utils';
import { AssignmentActions } from './assignment-actions';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger
} from '../../../shadcn-components/ui/tooltip';
import {
  AutomaticGradingBadge,
  CompletedAssignmentBadge,
  CreatedAssignmentBadge,
  FullyAutomaticGradingBadge,
  ManualGradingBadge,
  ReleasedAssignmentBadge
} from '../../ui/badges';

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

  const gradingType = () => {
    const gradingType = props.assignment.settings.autograde_type;
    if (gradingType === AutogradeTypeEnum.FullAuto) {
      return (
        <FullyAutomaticGradingBadge
          className={props.assignment.status === 'complete' ? 'opacity-80' : ''}
        />
      );
    } else if (gradingType === AutogradeTypeEnum.Auto) {
      return (
        <AutomaticGradingBadge
          className={props.assignment.status === 'complete' ? 'opacity-80' : ''}
        />
      );
    } else {
      return (
        <ManualGradingBadge
          className={props.assignment.status === 'complete' ? 'opacity-80' : ''}
        />
      );
    }
  };

  const assignmentStatus = () => {
    const status = props.assignment.status;
    switch (status) {
      case 'created':
        return <CreatedAssignmentBadge />;
      case 'pushed':
        return <CreatedAssignmentBadge />;
      case 'released':
        return <ReleasedAssignmentBadge />;
      case 'complete':
        return <CompletedAssignmentBadge />;
    }
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
            {assignmentStatus()}
            {gradingType()}
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
            'items-start flex-col justify-end gap-4 self-stretch bg-[#EBEBEB] p-4'
          }
        >
          <Button className={'w-full'}>Go to notebooks & files</Button>
          <Button className={'w-full'} variant={'outline'}>
            Go to submissions
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
};
