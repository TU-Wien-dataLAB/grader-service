import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
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

type PageItem = number | 'ellipsis-start' | 'ellipsis-end';

const MAX_VISIBLE = 5;

const range = (from: number, to: number) =>
  Array.from({ length: to - from + 1 }, (_, i) => from + i);

const getPageItems = (page: number, total: number): PageItem[] => {
  // Show everything if an ellipsis would not hide at least one page
  if (total <= MAX_VISIBLE + 2) {
    return range(1, total);
  }

  // Near the start: 1 2 3 4 5 … last
  if (page <= 3) {
    return [...range(1, MAX_VISIBLE), 'ellipsis-end', total];
  }

  // Near the end: 1 … last-4 … last
  if (page >= total - 2) {
    return [1, 'ellipsis-start', ...range(total - MAX_VISIBLE + 1, total)];
  }

  // In the middle: 1 … p-1 p p+1 … last
  return [1, 'ellipsis-start', page - 1, page, page + 1, 'ellipsis-end', total];
};

export const CustomPagination = (props: IPaginationProps) => {
  const { page, setPage, totalPages } = props;
  const items = getPageItems(page, totalPages);

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

        {items.map(item =>
          typeof item === 'number' ? (
            <PaginationItem key={item}>
              <PaginationLink
                isActive={item === page}
                onClick={() => setPage(item)}
              >
                {item}
              </PaginationLink>
            </PaginationItem>
          ) : (
            <PaginationItem key={item}>
              <PaginationEllipsis />
            </PaginationItem>
          )
        )}
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
