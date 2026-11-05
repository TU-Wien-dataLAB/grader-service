import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type FilterBy = 'active' | 'completed';
export type SortBy = { key?: string; dir: 'asc' | 'desc' };

type LectureFiltersState = {
  filterBy: FilterBy;
  sortBy: SortBy;
  page: number;
  perPage: number;
  searchQuery: string;

  setFilterBy: (f: FilterBy) => void;
  setSortBy: (s: SortBy) => void;
  setPage: (p: number) => void;
  setPerPage: (n: number) => void;
  setSearchQuery: (q: string) => void;
  reset: () => void;
};

const initialState = {
  filterBy: 'active' as FilterBy,
  sortBy: { dir: 'asc', key: 'name' } as SortBy,
  page: 1,
  perPage: 6,
  searchQuery: ''
};

export const useLectureFilters = create<LectureFiltersState>()(
  persist(
    set => ({
      ...initialState,

      // reset the page if any other parameter changes
      setFilterBy: filterBy => set({ filterBy, page: 1 }),
      setSortBy: sortBy => set({ sortBy, page: 1 }),
      setPage: page => set({ page }),
      setPerPage: perPage => set({ perPage, page: 1 }),
      setSearchQuery: searchQuery => set({ searchQuery, page: 1 }),
      reset: () => set(initialState)
    }),
    {
      name: 'lecture-filters',
      version: 1,
      partialize: s => ({
        filterBy: s.filterBy,
        sortBy: s.sortBy,
        perPage: s.perPage,
        searchQuery: s.searchQuery
      })
    }
  )
);
