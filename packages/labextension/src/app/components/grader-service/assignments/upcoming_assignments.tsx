import React from 'react';
import { UpcomingAssignmentCard } from './upcoming-assignment-card';
import { Pagination, PaginationContent, PaginationFirst, PaginationItem, PaginationLast, PaginationNext, PaginationPrevious } from '../../../shadcn-components/ui/pagination';
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from '../../../shadcn-components/ui/select';
import { getUpcomingAssignments } from '../../../../services/assignments.service';
import { useQuery } from '@tanstack/react-query';
import { EmptyState } from '../../utils/empty-state';
import { AllClearIcon } from '../../../../assets/all-clear-icon';


export const UpcomingAssignments = () => {
    const { data: assignments = [] } = useQuery({
      queryKey: ["assignments", "upcoming"],
      queryFn: () => getUpcomingAssignments(),
    });

    return (
    <div
      className={'flex flex-col h-full w-full overflow-hidden bg-background'}
      id={'upcoming-assignments-view'}
    >  
      <span className={'text-xl font-bold shrink-0 m-4 mb-0'}>
        Upcoming Assignments
      </span>
          
      {(assignments?.length != 0) ? (
      <div className={'flex flex-col flex-1 min-h-0 m-4 gap-4'}>
        <div className={'flex flex-col gap-2 flex-1 min-h-0 overflow-y-auto'}>
            {assignments.map((assignment) => (
              <UpcomingAssignmentCard key={assignment.id} assignment={assignment} />
            ))}
        </div>

        <div className="flex items-center justify-between gap-4 shrink-0">
              <Pagination>
                <PaginationContent>
                  <PaginationItem>
                    <PaginationFirst />
                  </PaginationItem>
                  <PaginationItem>
                    <PaginationPrevious />
                  </PaginationItem>
                  <PaginationItem>
                    
                  </PaginationItem>
                  <PaginationItem>
                    <PaginationNext />
                  </PaginationItem>
                  <PaginationItem>
                    <PaginationLast />
                  </PaginationItem>
                </PaginationContent>
              </Pagination>
              <Select defaultValue="6">
                <SelectTrigger id="select-rows-per-page">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent align="start">
                  <SelectGroup>
                    <SelectItem value="4">4 / Page</SelectItem>
                    <SelectItem value="6">6 / Page</SelectItem>
                    <SelectItem value="8">8 / Page</SelectItem>
                  </SelectGroup>
                </SelectContent>
              </Select>
            </div>
        </div>
      ):(
          <EmptyState
            title={'All clear!'}
            icon={<AllClearIcon />}
            description={
              'You have no upcoming assignments.'
            }
          />
      )}
      </div>
  );
}