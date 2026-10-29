import {
  Card,
  CardAction,
  CardContent,
  CardHeader,
  CardTitle
} from '../../../shadcn-components/ui/card';
import { Button } from '../../../shadcn-components/ui/button';
import { FileText, UserIcon } from 'lucide-react';
import { Link } from 'react-router';
import React from 'react';
import { IconTextInfo } from '../../ui/icon-text-info';
import { pluralize, highlightText } from '../../utils/utils';
import { EditLectureDialog } from './edit-lecture-dialog';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger
} from '../../../shadcn-components/ui/tooltip';
import { LectureListItemDto } from '../../../../model/lectureListItemDto';

export interface ILectureCard {
  lecture: LectureListItemDto;
  searchQuery?: string;
}

export const LectureCard = (props: ILectureCard) => {
  const lecture = props.lecture;
  return (
    <Card
      key={lecture.code}
      className={`relative p-4 gap-0 ${lecture.complete && 'text-border'}`}
    >
      <div className={'flex flex-row gap-2 mb-2'}>
        <CardHeader className={'self-stretch grow p-0'}>
          <div className={'min-w-0'}>
            <p className={'text-base font-bold'}>
              {highlightText(lecture.code, props.searchQuery)}
            </p>
            <Tooltip>
              <TooltipTrigger
                render={
                  <span className={'flex min-w-0'}>
                    <CardTitle {...props} className={'text-3xl line-clamp-2'}>
                      {highlightText(lecture.name, props.searchQuery)}
                    </CardTitle>
                  </span>
                }
              />
              <TooltipContent>
                <p>{lecture.name}</p>
              </TooltipContent>
            </Tooltip>
          </div>
          <CardAction className={'p-2'}>
            <EditLectureDialog lecture={lecture}></EditLectureDialog>
          </CardAction>
        </CardHeader>
      </div>
      <CardContent className={'flex flex-col gap-0.5 px-0 mb-4'}>
        {!lecture && (
          <IconTextInfo
            icon={
              <FileText
                className={'fill-foreground size-5 text-card! self-center'}
              />
            }
            text={`${lecture.assignment_count?.toString()} ${pluralize({
              text: 'Assignment',
              data: lecture.assignment_count
            })}`}
          />
        )}
        <IconTextInfo
          icon={
            <UserIcon
              className={'fill-foreground text-card! size-5 self-center'}
            />
          }
          text={`${lecture.student_count?.toString()} ${pluralize({
            text: 'Student',
            data: lecture.student_count
          })}`}
        />
      </CardContent>
      <Link to={`/lectures/${lecture.id}`}>
        <Button className={'w-fit'}>Details</Button>
      </Link>
    </Card>
  );
};
