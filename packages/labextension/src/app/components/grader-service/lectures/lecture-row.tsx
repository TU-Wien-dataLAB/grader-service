import { TableCell, TableRow } from '../../../shadcn-components/ui/table';
import { Button } from '../../../shadcn-components/ui/button';
import { FileText, UserIcon } from 'lucide-react';
import { Link } from 'react-router';
import React from 'react';
import { IconTextInfo } from '../../ui/icon-text-info';
import { EditLectureDialog } from './edit-lecture-dialog';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger
} from '../../../shadcn-components/ui/tooltip';
import { highlightText, pluralize } from '../../utils/utils';
import { LectureListItemDto } from '../../../../model/lectureListItemDto';

export interface ILectureRow {
  lecture: LectureListItemDto;
  searchQuery?: string;
}

export const LectureRow = (props: ILectureRow) => {
  const lecture = props.lecture;
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
        {!lecture && (
          <IconTextInfo
            icon={
              <FileText
                className={'fill-foreground size-5 text-white! self-center'}
              />
            }
            text={`${lecture.assignment_count?.toString()} ${pluralize({
              text: 'Assignment',
              data: lecture.assignment_count
            })}`}
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
          text={`${lecture.student_count?.toString()} ${pluralize({
            text: 'Student',
            data: lecture.student_count
          })}`}
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
