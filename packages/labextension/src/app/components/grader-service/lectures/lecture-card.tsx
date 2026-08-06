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
import { Lecture } from '../../../../model/lecture';
import { useQuery } from '@tanstack/react-query';
import { getUsers } from '../../../../services/lectures.service';
import { getAllAssignments } from '../../../../services/assignments.service';
import { IconTextInfo } from '../../ui/icon-text-info';
import { pluralize, highlightText } from '../../utils/utils';
import { User } from '../../../../model/user';
import { EditLectureDialog } from './edit-lecture-dialog';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger
} from '../../../shadcn-components/ui/tooltip';

export interface ILectureCard {
  lecture: Lecture;
  searchQuery?: string;
}

export const LectureCard = (props: ILectureCard) => {
  const lecture = props.lecture;
  const { data: users, isPending: isPendingUsers } = useQuery({
    queryKey: ['users', lecture.id],
    queryFn: async () => getUsers(lecture.id, false)
  });

  const { data: assignments, isPending: isPendingAssignments } = useQuery({
    queryKey: ['assignments', lecture.id],
    queryFn: async () => getAllAssignments(lecture.id, false, false)
  });

  let students: User[] = [];
  if (!isPendingUsers) {
    students = users.students;
  }
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
        {!isPendingAssignments && (
          <IconTextInfo
            icon={
              <FileText
                className={'fill-foreground size-5 text-white! self-center'}
              />
            }
            text={`${assignments.length.toString()} ${pluralize({
              text: 'Assignment',
              data: assignments
            })}`}
          />
        )}
        <IconTextInfo
          icon={
            <UserIcon
              className={'fill-foreground text-foreground! size-5 self-center'}
            />
          }
          text={`${students.length.toString()} ${pluralize({
            text: 'Student',
            data: students
          })}`}
        />
      </CardContent>
      <Link to={`/lectures/${lecture.id}`}>
        <Button className={'w-fit'}>Details</Button>
      </Link>
    </Card>
  );
};
