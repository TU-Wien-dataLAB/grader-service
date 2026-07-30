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

interface IFilterLecturesButtonProps {
  className?: string;
  filterBy: string;
  setFilterBy: React.Dispatch<React.SetStateAction<string>>;
}

export const FilterLecturesButton = (props: IFilterLecturesButtonProps) => {
  return (
    <DropdownMenu modal={false}>
      <DropdownMenuTrigger>
        <Button variant={'link'} className={'p-2 justify-self-end underline'}>
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
  filterGroups: Record<
    string,
    {
      key: string;
      value: string;
      label: string;
    }[]
  >;
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
      <DropdownMenuContent>
        {props.filterGroups &&
          Object.entries(props.filterGroups)?.map(([groupKey, filters]) => (
            <DropdownMenuGroup key={groupKey}>
              <DropdownMenuLabel>{groupKey}</DropdownMenuLabel>
              {filters.map(filter => (
                <DropdownMenuCheckboxItem
                  key={`${filter.key}:${filter.value}`}
                  checked={props.activeFilters.has(
                    `${filter.key}:${filter.value}:${filter.label}`
                  )}
                  onCheckedChange={() =>
                    props.toggle(filter.key, filter.value, filter.label)
                  }
                >
                  {filter.label}
                </DropdownMenuCheckboxItem>
              ))}
            </DropdownMenuGroup>
          ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
};
