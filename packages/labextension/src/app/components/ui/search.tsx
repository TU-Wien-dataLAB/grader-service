import { Button } from '../../shadcn-components/ui/button';
import { Search } from 'lucide-react';
import React, { useEffect, useState } from 'react';
import { ButtonGroup } from '../../shadcn-components/ui/button-group';
import { loadObject, storeObject } from '../../../services/storage.service';
import {
  Autocomplete,
  AutocompleteContent,
  AutocompleteEmpty,
  AutocompleteInput,
  AutocompleteItem,
  AutocompleteList
} from '../../shadcn-components/ui/autocomplete';

export interface ISearchField {
  placeholder?: string;
  recentSearchesKey?: string;
  searchQuery: string;
  setSearchQuery: React.Dispatch<React.SetStateAction<string>>;
}
export const SearchField = (props: ISearchField) => {
  const [query, setQuery] = useState('');
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [isOpen, setIsOpen] = useState(false);

  // Recent searches logic
  useEffect(() => {
    const history: string[] | null = loadObject(props.recentSearchesKey) ?? [];
    setRecentSearches(history);
  }, []);

  const handleNewSearch = () => {
    if (query.trim() === '') {
      return;
    }
    const history: string[] = loadObject(props.recentSearchesKey);
    let updated = [];
    if (history === null) {
      updated.push(query);
    } else {
      updated = [...history.filter(q => q !== query), query];
      if (updated.length > 5) {
        updated.shift();
      }
    }
    setRecentSearches(updated);
    storeObject(props.recentSearchesKey, updated);
  };
  const handleFocus = () => {
    setSuggestions(query.trim() === '' ? recentSearches : suggestions);
    setIsOpen(true);
  };
  // handle input logic
  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    props.setSearchQuery(query);
    handleNewSearch();
    setIsOpen(false);
  };

  const handleValueChange = (value: string) => {
    setQuery(value);
    if (value.trim() === '') {
      setSuggestions(recentSearches);
    } else {
      setSuggestions([]);
    }
    setIsOpen(true);
  };

  return (
    <Autocomplete
      items={suggestions}
      open={isOpen}
      onOpenChange={setIsOpen}
      value={query}
      onValueChange={handleValueChange}
      submitOnItemClick={true}
    >
      <ButtonGroup
        className={
          'border border-border min-w-0 max-w-80 rounded-xs has-active:border-primary has-focus:ring-2 has-focus:ring-primary has-focus:ring-offset-2 focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2'
        }
      >
        <form onSubmit={handleSubmit} className={'flex'} id={'search-form'}>
          <AutocompleteInput
            showClear
            onFocus={handleFocus}
            onBlur={() => setIsOpen(false)}
            placeholder={props?.placeholder}
          />
          <Button
            variant={'outline'}
            size="icon"
            interactive={false}
            type={'submit'}
            className={
              'bg-sidebar-ring border-none rounded-none text-primary p-2'
            }
          >
            <Search className={'size-4'} />
          </Button>
        </form>
      </ButtonGroup>
      <AutocompleteContent>
        <AutocompleteEmpty>No results found.</AutocompleteEmpty>
        <AutocompleteList>
          {item => (
            <AutocompleteItem key={item} value={item}>
              {item}
            </AutocompleteItem>
          )}
        </AutocompleteList>
      </AutocompleteContent>
    </Autocomplete>
  );
};
