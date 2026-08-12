import { useEffect, useState } from 'react';

import { ChevronDownIcon, CirclePlus, X } from 'lucide-react';

import { Button } from './button';
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList
} from './command';
import { Popover, PopoverContent, PopoverTrigger } from './popover';
import { cn } from '../../lib/utils';
import React from 'react';
import { AnyFieldApi } from '@tanstack/react-form';

export type ComboboxOptions = {
  value: string;
  label: string;
};

interface IComboboxProps {
  options: ComboboxOptions[];
  selected: ComboboxOptions['value'];
  className?: string;
  placeholder?: string;
  disalbed?: boolean;
  onChange: (option: ComboboxOptions) => void;
  onCreate?: (label: ComboboxOptions['label']) => void;
  field: AnyFieldApi;
}

/**
 * CommandItem to create a new query content
 *
 */
function CommandAddItem({
  query,
  onCreate
}: {
  query: string;
  onCreate: () => void;
}) {
  return (
    <div
      tabIndex={0}
      onClick={onCreate}
      onKeyDown={(event: React.KeyboardEvent<HTMLDivElement>) => {
        if (event.key === 'Enter') {
          onCreate();
        }
      }}
      className={cn(
        'flex w-full cursor-pointer text-sm px-2 py-1.5 rounded-xs items-center focus:outline-none'
      )}
    >
      <CirclePlus className="mr-2 h-4 w-4" />
      Create "{query}"
    </div>
  );
}

export function Combobox({
  options,
  selected,
  className,
  placeholder,
  disalbed,
  onChange,
  onCreate,
  field
}: IComboboxProps) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');

  const [canCreate, setCanCreate] = useState(true);
  useEffect(() => {
    // Cannot create a new query if it is empty or has already been created
    // Unlike search, case sensitive here.
    const isAlreadyCreated = !options.some(option => option.label === query);
    setCanCreate(!!(query && isAlreadyCreated));
  }, [query, options]);

  function handleSelect(option: ComboboxOptions) {
    if (onChange) {
      onChange(option);
      field.handleChange(option.value);
      setOpen(false);
      setQuery('');
    }
  }

  function handleCreate() {
    if (onCreate && query) {
      onCreate(query);
      field.handleChange(query);
      setOpen(false);
      setQuery('');
    }
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger>
        <Button
          type="button"
          variant="outline"
          role="combobox"
          disabled={disalbed ?? false}
          aria-expanded={open}
          className={cn(
            'w-full font-normal pr-0 border border-border',
            className
          )}
        >
          {selected && selected.length > 0 ? (
            <div className="truncate mr-auto">
              {options.find(item => item.value === selected)?.label}
            </div>
          ) : (
            <div className="text-slate-600 mr-auto">
              {placeholder ?? 'Select'}
            </div>
          )}
          <span className="flex items-center">
            {selected && (
              <span
                role="button"
                tabIndex={0}
                onClick={e => {
                  e.stopPropagation();
                  handleSelect({ value: '', label: '' });
                }}
                className="inline-flex size-6 items-center text-primary justify-center hover:opacity-70"
              >
                <X className="size-3.5" />
              </span>
            )}{' '}
          </span>
          <ChevronDownIcon className="pointer-events-none [&]:size-auto self-stretch w-8 text-primary p-2 bg-sidebar-ring" />{' '}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-full p-0">
        <Command className={'p-0'}>
          <CommandInput
            placeholder="Search or create new"
            value={query}
            onValueChange={(value: string) => setQuery(value)}
            onKeyDown={(event: React.KeyboardEvent<HTMLInputElement>) => {
              if (event.key === 'Enter') {
                // Avoid selecting what is displayed as a choice even if you press Enter for the conversion
                // Note that if you do this, you can select a choice with the arrow keys and press Enter, but it will not be selected
                event.preventDefault();
              }
            }}
          />
          <CommandEmpty className="flex pl-1 py-1 w-full">
            {query && (
              <CommandAddItem query={query} onCreate={() => handleCreate()} />
            )}
          </CommandEmpty>

          <CommandList>
            <CommandGroup className="overflow-y-auto p-0">
              {/* No options and no query */}
              {/* Even if written as a Child of CommandEmpty, it may not be displayed only the first time, so write it in CommandGroup. */}
              {options.length === 0 && !query && (
                <div className="py-1.5 pl-8 space-y-1 text-sm">
                  <p>No items</p>
                  <p>Enter a value to create a new one</p>
                </div>
              )}

              {/* Create */}
              {canCreate && (
                <CommandAddItem query={query} onCreate={() => handleCreate()} />
              )}

              {/* Select */}
              {options.map((option, index) => (
                <CommandItem
                  key={option.label}
                  tabIndex={0}
                  value={option.label}
                  onSelect={() => {
                    handleSelect(option);
                  }}
                  onKeyDown={(event: React.KeyboardEvent<HTMLDivElement>) => {
                    if (event.key === 'Enter') {
                      event.stopPropagation();
                      handleSelect(option);
                    }
                  }}
                  className={'cursor-pointer'}
                >
                  {option.label}
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
