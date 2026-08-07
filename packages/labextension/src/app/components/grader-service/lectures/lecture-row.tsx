import { Lecture } from '../../../../model/lecture';
import { TableCell, TableRow } from '../../../shadcn-components/ui/table';
import { Button } from '../../../shadcn-components/ui/button';
import { FileText, UserIcon } from 'lucide-react';
import { Link } from 'react-router';
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { getLectureUsers } from '../../../../services/lectures.service';
import { getAllAssignments } from '../../../../services/assignments.service';
import { IconTextInfo } from '../../ui/icon-text-info';
import { User } from '../../../../model/user';
import { EditLectureDialog } from './edit-lecture-dialog';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger
} from '../../../shadcn-components/ui/tooltip';
import { highlightText } from '../../utils/utils';

export interface ILectureRow {
  lecture: Lecture;
  searchQuery?: string;
}

export const LectureRow = (props: ILectureRow) => {
  const lecture = props.lecture;

  const { data: users, isPending: isPendingUsers } = useQuery({
    queryKey: ['users', lecture.id],
    queryFn: async () => getLectureUsers(lecture.id, false)
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
    <TableRow
      key={lecture.id}
      className={`py-4 px-0 ${lecture.complete && 'text-border'}`}
    >
      <TableCell className={'font-bold'}>
        {highlightText(lecture.code, props.searchQuery)}
      </TableCell>
      <Tooltip>
        <TooltipTrigger
          render={
            <span className={'flex w-fit'}>
              <TableCell
                {...props}
                className={'font-bold text-lg truncate max-w-50'}
              >
                {highlightText(lecture.name, props.searchQuery)}
              </TableCell>
            </span>
          }
        ></TooltipTrigger>
        <TooltipContent>
          <p>{lecture.name}</p>
        </TooltipContent>
      </Tooltip>
      <TableCell>
        {!isPendingAssignments && (
          <IconTextInfo
            icon={
              <FileText
                className={'fill-foreground size-5 text-white! self-center'}
              />
            }
            text={assignments.length.toString()}
          />
        )}
      </TableCell>
      <TableCell>
        <IconTextInfo
          icon={
            <UserIcon
              className={'fill-foreground size-5 text-foreground! self-center'}
            />
          }
          text={students.length.toString()}
        />
      </TableCell>

      <TableCell>
        <Link to={`/lectures/${lecture.id}`}>
          <Button className={'w-fit'}>Details</Button>
        </Link>
      </TableCell>
      <TableCell>
        <EditLectureDialog lecture={lecture} />
      </TableCell>
    </TableRow>
  );
};
