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
  setPage: (page: number) => void;
  totalPages: number;
}

export const CustomPagination = (props: IPaginationProps) => {
  const { page, setPage, totalPages } = props;
  return (
    <Pagination>
      <PaginationContent>
        <PaginationItem>
          <PaginationFirst
            disabled={page === 1}
            isActive={page !== 1}
            onClick={() => setPage(1)}
          />
        </PaginationItem>
        <PaginationItem>
          <PaginationPrevious
            disabled={page === 1}
            isActive={page !== 1}
            onClick={() => setPage(Math.max(1, page - 1))}
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
            disabled={page === totalPages}
            isActive={page !== totalPages}
            onClick={() => setPage(Math.min(totalPages, page + 1))}
          />
        </PaginationItem>
        <PaginationItem>
          <PaginationLast
            disabled={page === totalPages}
            isActive={page !== totalPages}
            onClick={() => setPage(totalPages)}
          />
        </PaginationItem>
      </PaginationContent>
    </Pagination>
  );
};
