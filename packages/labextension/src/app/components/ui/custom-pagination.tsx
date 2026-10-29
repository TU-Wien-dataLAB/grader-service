import {
  Pagination,
  PaginationContent,
  PaginationFirst,
  PaginationItem,
  PaginationLast,
  PaginationLink,
  PaginationNext,
  PaginationPrevious
} from '../../shadcn-components/ui/pagination';
import React from 'react';

interface IPaginationProps {
  page: number;
  setPage: React.Dispatch<React.SetStateAction<number>>;
  totalPages: number;
}

export const CustomPagination = (props: IPaginationProps) => {
  const { page, setPage, totalPages } = props;
  return (
    <Pagination>
      <PaginationContent>
        <PaginationItem>
          <PaginationFirst isActive={page !== 1} onClick={() => setPage(1)} />
        </PaginationItem>
        <PaginationItem>
          <PaginationPrevious
            isActive={page !== 1}
            onClick={() => setPage(prev => prev - 1)}
          />
        </PaginationItem>
        <PaginationItem>
          {Array.from({ length: totalPages }, (_, i) => (
            <PaginationLink
              key={i}
              isActive={i + 1 === page}
              onClick={() => setPage(i + 1)}
            >
              {i + 1}
            </PaginationLink>
          ))}
        </PaginationItem>
        <PaginationItem>
          <PaginationNext
            isActive={page !== totalPages}
            onClick={() => setPage(prev => prev + 1)}
          />
        </PaginationItem>
        <PaginationItem>
          <PaginationLast
            isActive={page !== totalPages}
            onClick={() => setPage(totalPages)}
          />
        </PaginationItem>
      </PaginationContent>
    </Pagination>
  );
};
