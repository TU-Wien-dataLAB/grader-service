import React from 'react';
import { Button } from '../../shadcn-components/ui/button';
import { ListFilter } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger
} from '../../shadcn-components/ui/dropdown-menu';
import { IFilterGroup } from '../../pages/instructor-view/lecture';

interface IFilterLecturesButtonProps {
  className?: string;
  filterBy: string;
  setFilterBy: React.Dispatch<React.SetStateAction<string>>;
}

export const FilterLecturesButton = (props: IFilterLecturesButtonProps) => {
  return (
    <DropdownMenu modal={false}>
      <DropdownMenuTrigger>
        <Button
          data-testid="filter-btn"
          variant={'link'}
          className={'p-2 justify-self-end underline'}
        >
          <ListFilter className={'text-primary size-4 justify-self-center'} />
          Filter
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align={'start'}>
        <DropdownMenuGroup>
          <DropdownMenuLabel>Status</DropdownMenuLabel>
          <DropdownMenuItem onClick={() => props.setFilterBy('active')}>
            Active
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => props.setFilterBy('completed')}>
            Completed
          </DropdownMenuItem>
        </DropdownMenuGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

interface IFilterAssignmentsButtonProps {
  allFilters: IFilterGroup[];
  activeFilters: Set<string>;
  toggle: (key: string, value: string, label: string) => void;
}

export const FilterAssignmentsButton = (
  props: IFilterAssignmentsButtonProps
) => {
  return (
    <DropdownMenu modal={false}>
      <DropdownMenuTrigger>
        <Button variant={'link'} className={'p-1 justify-self-end'}>
          <ListFilter className={'text-primary size-5 justify-self-center'} />
          Filter
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align={'end'}>
        {props.allFilters &&
          props.allFilters.map(group =>
            Object.entries(group).map(([category, filterProperties]) => (
              <DropdownMenuGroup key={category}>
                <DropdownMenuLabel>{category}</DropdownMenuLabel>
                {filterProperties.map(filter => (
                  <DropdownMenuCheckboxItem
                    key={`${category}:${filter.value}`}
                    checked={props.activeFilters.has(
                      `${category}:${filter.value}:${filter.label}`
                    )}
                    onCheckedChange={() =>
                      props.toggle(category, filter.value, filter.label)
                    }
                  >
                    {filter.label}
                  </DropdownMenuCheckboxItem>
                ))}
              </DropdownMenuGroup>
            ))
          )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
};
