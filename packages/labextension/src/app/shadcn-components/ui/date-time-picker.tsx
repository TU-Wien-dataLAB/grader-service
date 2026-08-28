'use client';

import * as React from 'react';
import { format } from 'date-fns';
import { Calendar as CalendarIcon, Clock2Icon, X } from 'lucide-react';

import { Button } from './button';
import { Calendar } from './calendar';
import { Field, FieldGroup, FieldLabel } from './field';
import { Popover, PopoverContent, PopoverTrigger } from './popover';
import { AnyFieldApi } from '@tanstack/react-form';
import { InputGroup, InputGroupAddon, InputGroupInput } from './input-group';

interface IDatePickerTime {
  open: boolean;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
  field: AnyFieldApi;
}

export function DatePickerTime(props: IDatePickerTime) {
  const date = props.field.state.value as Date | undefined;

  const handleDateSelect = (selected: Date | undefined) => {
    if (!selected) {
      return;
    }

    props.field.handleChange(selected.toISOString());
    props.setOpen(false);
  };

  const handleTimeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const [hours, minutes, seconds] = e.target.value.split(':').map(Number);
    const updated = date ? new Date(date) : new Date();
    updated.setHours(hours, minutes, seconds ?? 0);
    props.field.handleChange(updated.toISOString());
  };

  const deleteDate = () => {
    handleDateSelect(undefined);
    props.field.handleChange(null);
  };
  return (
    <FieldGroup className="mx-auto flex-row">
      <Field className={'flex-1'}>
        <FieldLabel htmlFor="date-picker-optional">Date</FieldLabel>
        <Popover open={props.open} onOpenChange={props.setOpen}>
          <PopoverTrigger
            render={
              <Button
                variant="outline"
                id="date-picker-optional"
                className="justify-between font-normal border-border border px-0 pl-2.5 hover:bg-input active:bg-input"
              >
                {date ? format(date, 'PPP') : 'Select date'}
                <span className="flex items-center">
                  {date && (
                    <span
                      role="button"
                      tabIndex={0}
                      onClick={e => {
                        e.stopPropagation();
                        deleteDate();
                      }}
                      className="inline-flex size-6 items-center text-primary justify-center hover:opacity-70"
                    >
                      <X className="size-3.5" />
                    </span>
                  )}
                  <CalendarIcon
                    data-icon="inline-end"
                    className="text-primary size-7 p-1.5 bg-sidebar-ring"
                  />
                </span>
              </Button>
            }
          />
          <PopoverContent className="w-auto overflow-hidden p-0" align="start">
            <Calendar
              mode="single"
              selected={date}
              captionLayout="dropdown"
              defaultMonth={date}
              onSelect={handleDateSelect}
            />
          </PopoverContent>
        </Popover>
      </Field>
      <Field className="flex-1">
        <FieldLabel htmlFor="time-picker-optional">Time</FieldLabel>
        <InputGroup>
          <InputGroupInput
            type="time"
            id="time-picker-optional"
            step="1"
            value={date ? format(date, 'HH:mm:ss') : '00:00:00'}
            onChange={handleTimeChange}
            placeholder="HH:MM"
            className="appearance-none [&::-webkit-calendar-picker-indicator]:hidden [&::-webkit-calendar-picker-indicator]:appearance-none"
          />
          <InputGroupAddon align={'inline-end'} className={'p-1.5'}>
            <Clock2Icon className="fill-primary size-4" />
          </InputGroupAddon>
        </InputGroup>
      </Field>
    </FieldGroup>
  );
}
