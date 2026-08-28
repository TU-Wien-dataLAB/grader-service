import React, { useState } from 'react';
import { Button } from '../../shadcn-components/ui/button';
import { ArrowUpDown } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger
} from '../../shadcn-components/ui/dropdown-menu';

interface ISortButtonProps {
  className?: string;
  sortBy: { key: string; dir: string };
  setSortBy: React.Dispatch<React.SetStateAction<{ key: string; dir: string }>>;
}

export const SortButton = (props: ISortButtonProps) => {
  const [sortValue, setSortValue] = useState('');
  const handleSortChange = (value: string) => {
    setSortValue(value);
    switch (value) {
      case 'date-new-to-old':
        props.setSortBy({ key: 'date', dir: 'desc' });
        break;
      case 'date-old-to-new':
        props.setSortBy({ key: 'date', dir: 'asc' });
        break;
      case 'title-a-z':
        props.setSortBy({ key: 'name', dir: 'asc' });
        break;
      case 'title-z-a':
        props.setSortBy({ key: 'name', dir: 'desc' });
        break;
    }
  };
  return (
    <div className={`flex flex-row justify-center`}>
      <DropdownMenu modal={false}>
        <DropdownMenuTrigger>
          <Button
            variant={'link'}
            className={'px-2 justify-self-end underline'}
          >
            <ArrowUpDown
              className={'text-primary size-4 justify-self-center'}
            />
            Sort
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent>
          <DropdownMenuRadioGroup
            value={sortValue}
            onValueChange={handleSortChange}
          >
            <DropdownMenuRadioItem value={'date-new-to-old'}>
              Date: new to old
            </DropdownMenuRadioItem>
            <DropdownMenuRadioItem value={'date-old-to-new'}>
              Date: old to new
            </DropdownMenuRadioItem>
            <DropdownMenuRadioItem value={'title-a-z'}>
              Title: A-Z
            </DropdownMenuRadioItem>
            <DropdownMenuRadioItem value={'title-z-a'}>
              Title: Z-A
            </DropdownMenuRadioItem>
          </DropdownMenuRadioGroup>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
};
