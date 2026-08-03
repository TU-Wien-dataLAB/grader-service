import React, { useState } from 'react';
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle
} from '../../../shadcn-components/ui/dialog';
import { Assignment } from '../../../../model/assignment';
import { AnyFieldApi, useForm, useStore } from '@tanstack/react-form';
import { Input } from '../../../shadcn-components/ui/input';
import {
  Field,
  FieldGroup,
  FieldLabel
} from '../../../shadcn-components/ui/field';
import {
  ComboboxContent,
  ComboboxInput,
  ComboboxList,
  ComboboxItem,
  useComboboxAnchor
} from '../../../shadcn-components/ui/combobox';
import {
  ComboboxItemCreatable,
  CreatableCombobox,
  isCreatableItem
} from '../../../shadcn-components/ui/creatable-combobox';
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '../../../shadcn-components/ui/select';
import { AssignmentSettings } from '../../../../model/assignmentSettings';
import AutogradeTypeEnum = AssignmentSettings.AutogradeTypeEnum;
import { DatePickerTime } from '../../../shadcn-components/ui/date-time-picker';
import { Button } from '../../../shadcn-components/ui/button';
import {
  CalendarIcon,
  CirclePlus,
  ClockIcon,
  Info,
  PlusIcon,
  TrashIcon,
  XIcon
} from 'lucide-react';
import { Badge } from '../../../shadcn-components/ui/badge';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger
} from '../../../shadcn-components/ui/tooltip';
import {
  CELL_TIMEOUT,
  GRADING_METHOD,
  LATE_SUBMISSIONS,
  WHITELIST_FILE_PATTERNS
} from './static/assignment-metadata-explainations';
import {
  calculateDaysDifference,
  determineDisplayText,
  buildPeriod
} from '../../utils/utils';
import moment from 'moment';
import { useGroups } from '../../../pages/instructor-view/lecture';
import { Checkbox } from '../../../shadcn-components/ui/checkbox';
import { useAssignmentUpdate } from '../../../hooks/assignment/assignment-update-hook';
import { useAssignmentCreate } from '../../../hooks/assignment/assignment-create-hook';
import { Separator } from '../../../shadcn-components/ui/separator';
import {
  InputGroup,
  InputGroupAddon,
  InputGroupInput
} from '../../../shadcn-components/ui/input-group';

interface IAssignmentSettingsForm {
  assignment?: Assignment;
  lectureId?: number;
  openDialog: boolean;
  setOpenDialog: React.Dispatch<React.SetStateAction<boolean>>;
}
const GRADING_METHODS = [
  { label: 'Automatic Grading', value: AutogradeTypeEnum.Auto },
  { label: 'Fully Automatic Grading', value: AutogradeTypeEnum.FullAuto },
  { label: 'Manual Grading', value: AutogradeTypeEnum.Unassisted }
];

export const AssignmentSettingsDialog = (props: IAssignmentSettingsForm) => {
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [recalcScoresConfirmed, setRecalcScoresConfirmed] = useState(false);
  const { handleUpdateAssignment } = useAssignmentUpdate();
  const { handleCreateAssignment } = useAssignmentCreate();
  const { groups, addCustomGroup } = useGroups();
  const form = useForm({
    defaultValues: {
      title: props.assignment?.name,
      group: props.assignment?.settings?.group,
      grading_method: props.assignment?.settings?.autograde_type,
      deadline: props.assignment?.settings?.deadline,
      late_submissions: props.assignment?.settings?.late_submission,
      number_of_submissions: props.assignment?.settings?.max_submissions,
      cell_timeout: props.assignment?.settings?.cell_timeout,
      allowed_file_patterns: props.assignment?.settings?.allowed_files
    },
    onSubmit: async ({ value }) => {
      const newAssignment: Assignment = {
        name: value.title,
        settings: {
          group: value.group,
          deadline: value.deadline,
          max_submissions: value.number_of_submissions,
          allowed_files: value.allowed_file_patterns,
          autograde_type: value.grading_method,
          cell_timeout: value.cell_timeout,
          late_submission: value.late_submissions
        }
      };

      if (!createAnother) {
        props.setOpenDialog(false);
      }
      if (props.assignment) {
        await handleUpdateAssignment(
          props.assignment,
          newAssignment,
          props.lectureId
        );
      } else {
        await handleCreateAssignment(newAssignment, props.lectureId);
      }
    }
  });
  // storing whitelist_patterns allows us to re-render the DOM when pattern list changes
  const whitelist_patterns = useStore(
    form.store,
    state => state.values.allowed_file_patterns
  );

  const [deadlineOpen, setDeadlineOpen] = React.useState<boolean>(false);
  const [createAnother, setCreateAnother] = useState(false);
  const [whitelistPatternsInput, setWhitelistPatternsInput] = useState('');
  const handleAddAllowedFilePattern = (field: AnyFieldApi) => {
    if (
      whitelistPatternsInput.trim().length > 0 &&
      !form.state.values?.allowed_file_patterns?.includes(
        whitelistPatternsInput
      )
    ) {
      field.pushValue(whitelistPatternsInput);
      setWhitelistPatternsInput('');
    }
  };
  const anchor = useComboboxAnchor();

  return (
    <Dialog open={props.openDialog} onOpenChange={props.setOpenDialog}>
      <DialogContent className={'overflow-y-auto'}>
        <DialogHeader>
          <DialogTitle>
            {props.assignment
              ? `Edit ${props.assignment.name}`
              : 'New Assignment'}
          </DialogTitle>
        </DialogHeader>
        <Separator />
        <form
          id={'create-edit-assignment-form'}
          onKeyDown={e => {
            const target = e.target as HTMLElement;
            if (e.key === 'Enter' && target.id !== 'allowed_file_patterns') {
              e.preventDefault();
            }
          }}
          onSubmit={e => {
            e.preventDefault();
            e.stopPropagation();
            form.handleSubmit();
          }}
        >
          <FieldGroup className={'flex p-6 items-start gap-4 self-stretch'}>
            <form.Field
              name={'title'}
              validators={{
                onChange: ({ value }) => {
                  if (value.length > 255) {
                    return 'Title is too long.';
                  } else if (value.trim().length === 0) {
                    return 'Title is empty.';
                  }
                  return undefined;
                }
              }}
              children={field => {
                return (
                  <Field>
                    <FieldLabel htmlFor={field.name}>Title *</FieldLabel>
                    <Input
                      id={field.name}
                      name={field.name}
                      value={field.state.value ?? null}
                      onChange={e => field.handleChange(e.target.value)}
                      required
                    ></Input>
                    {!field.state.meta.isValid && (
                      <em role={'alertdialog'} className={'text-red-700'}>
                        {field.state.meta.errors.join(', ')}
                      </em>
                    )}
                  </Field>
                );
              }}
            />
            <form.Field
              name={'grading_method'}
              children={field => {
                return (
                  <Field>
                    <div className={'flex flex-row gap-1.5'}>
                      <FieldLabel htmlFor={field.name}>
                        Grading method *
                      </FieldLabel>
                      <Tooltip>
                        <TooltipTrigger>
                          <Info
                            className={'size-4 fill-primary text-background'}
                          />
                        </TooltipTrigger>
                        <TooltipContent>{GRADING_METHOD}</TooltipContent>
                      </Tooltip>
                    </div>
                    <Select
                      items={GRADING_METHODS}
                      onValueChange={field.handleChange}
                      value={field.state.value ?? AutogradeTypeEnum.Auto}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectGroup>
                          {GRADING_METHODS.map(item => (
                            <SelectItem key={item.value} value={item.value}>
                              {item.label}
                            </SelectItem>
                          ))}
                        </SelectGroup>
                      </SelectContent>
                    </Select>
                  </Field>
                );
              }}
            />
            <form.Field
              name={'group'}
              children={field => {
                return (
                  <Field>
                    <FieldLabel htmlFor={field.name}>Group</FieldLabel>
                    <CreatableCombobox
                      items={groups}
                      onCreateValue={value => addCustomGroup(value)}
                      onValueChange={value =>
                        field.handleChange(value as string)
                      }
                    >
                      <div ref={anchor}>
                        <ComboboxInput
                          placeholder="Select or create a group"
                          value={field.state.value ?? null}
                        />
                      </div>
                      <ComboboxContent anchor={anchor}>
                        <ComboboxList>
                          {item =>
                            isCreatableItem(item) ? (
                              <ComboboxItemCreatable
                                value={item}
                                key={'__create__'}
                              />
                            ) : (
                              <ComboboxItem value={item} key={item}>
                                {item}
                              </ComboboxItem>
                            )
                          }
                        </ComboboxList>
                      </ComboboxContent>
                    </CreatableCombobox>
                  </Field>
                );
              }}
            />
            <form.Field
              name={'deadline'}
              validators={{
                onChange: ({ value }) => {
                  if (!value) {
                    return;
                  }
                  const chosenDate = new Date(value);
                  if (chosenDate < new Date()) {
                    return 'Deadline must be in the future.';
                  }
                }
              }}
              children={field => {
                let dayDiff;
                return (
                  <div className={'flex flex-col w-full'}>
                    <DatePickerTime
                      open={deadlineOpen}
                      setOpen={setDeadlineOpen}
                      field={field}
                    />
                    {field.state.value &&
                      field.state.meta.isTouched &&
                      field.state.meta.isValid && (
                        <p className={'text-base text-green-700 italic'}>
                          Deadline is in{' '}
                          {
                            (dayDiff = calculateDaysDifference({
                              startDate: new Date(field.state.value),
                              endDate: new Date()
                            }))
                          }{' '}
                          {determineDisplayText({ text: 'day', data: dayDiff })}
                        </p>
                      )}
                    {!field.state.meta.isValid && (
                      <em className={'text-red-700'}>
                        {field.state.meta.errors.join(', ')}
                      </em>
                    )}
                  </div>
                );
              }}
            />
            <form.Field name={'late_submissions'} mode={'array'}>
              {field => {
                return (
                  <Field>
                    <div className={'flex flex-row gap-1.5'}>
                      <FieldLabel>Late Submissions</FieldLabel>
                      <Tooltip>
                        <TooltipTrigger>
                          <Info
                            className={'size-4 fill-primary text-background'}
                          />
                        </TooltipTrigger>
                        <TooltipContent>{LATE_SUBMISSIONS}</TooltipContent>
                      </Tooltip>
                    </div>
                    {field.state.value?.length > 0 &&
                      field.state.value.map((submissionPeriod, index) => {
                        const isDisabled = !form.state.values.deadline;

                        return (
                          <>
                            <div
                              className={
                                'flex flex-row items-end gap-4 self-stretch'
                              }
                              key={index}
                            >
                              <form.Field
                                name={`late_submissions[${index}].period`}
                              >
                                {subField => {
                                  const period = subField.state.value
                                    ? moment.duration(subField.state.value)
                                    : null;
                                  const days = period?.days() ?? undefined;
                                  const hours = period?.hours() ?? undefined;
                                  return (
                                    <>
                                      <InputGroup>
                                        <InputGroupInput
                                          id={`${subField.name}-days`}
                                          name={`${subField.name}-days`}
                                          type={'number'}
                                          min={0}
                                          placeholder={'Days'}
                                          disabled={isDisabled}
                                          value={days}
                                          onChange={e =>
                                            subField.handleChange(
                                              buildPeriod(
                                                Number(e.target.value),
                                                hours ?? 0
                                              )
                                            )
                                          }
                                        />
                                        <InputGroupAddon
                                          align={'inline-end'}
                                          className={'p-1.5'}
                                        >
                                          <CalendarIcon className="size-4 text-primary bg-sidebar-ring" />
                                        </InputGroupAddon>
                                      </InputGroup>
                                      <InputGroup>
                                        <InputGroupInput
                                          id={`${subField.name}-hours`}
                                          name={`${subField.name}-hours`}
                                          type={'number'}
                                          min={0}
                                          placeholder={'Hours'}
                                          disabled={isDisabled}
                                          value={hours}
                                          onChange={e =>
                                            subField.handleChange(
                                              buildPeriod(
                                                days ?? 0,
                                                Number(e.target.value)
                                              )
                                            )
                                          }
                                        />
                                        <InputGroupAddon
                                          align={'inline-end'}
                                          className={'p-1.5'}
                                        >
                                          <ClockIcon className="size-4 text-primary bg-sidebar-ring" />
                                        </InputGroupAddon>
                                      </InputGroup>
                                    </>
                                  );
                                }}
                              </form.Field>
                              <form.Field
                                name={`late_submissions[${index}].scaling`}
                              >
                                {subField => {
                                  return (
                                    <Input
                                      id={subField.name}
                                      name={subField.name}
                                      type={'number'}
                                      min={0}
                                      max={1}
                                      step={0.01}
                                      placeholder={'Scaling'}
                                      disabled={isDisabled}
                                      value={
                                        (subField.state.value as number) ??
                                        undefined
                                      }
                                      onChange={e =>
                                        subField.handleChange(
                                          Number(e.target.value)
                                        )
                                      }
                                    />
                                  );
                                }}
                              </form.Field>
                              <Button
                                type="button"
                                variant="link"
                                onClick={() => field.removeValue(index)}
                              >
                                <TrashIcon className="size-4" />
                              </Button>
                            </div>
                          </>
                        );
                      })}
                    <Tooltip open={!form.state.values?.deadline ? null : false}>
                      <TooltipTrigger
                        render={
                          <span>
                            <Button
                              type="button"
                              variant="outline"
                              className="w-full"
                              disabled={!form.state.values?.deadline}
                              onClick={() =>
                                field.pushValue({
                                  period: undefined,
                                  scaling: undefined
                                })
                              }
                            >
                              <PlusIcon className="size-4" /> Add late
                              submission period
                            </Button>
                          </span>
                        }
                      ></TooltipTrigger>
                      <TooltipContent>
                        No deadline has been chosen.
                      </TooltipContent>
                    </Tooltip>
                  </Field>
                );
              }}
            </form.Field>
            <form.Field
              name={'number_of_submissions'}
              children={field => {
                return (
                  <Field>
                    <FieldLabel htmlFor={field.name}>
                      Number of submissions
                    </FieldLabel>
                    <Input
                      id={field.name}
                      name={field.name}
                      type={'number'}
                      min={1}
                      value={field.state.value ?? undefined}
                      onChange={e => field.handleChange(Number(e.target.value))}
                    />
                  </Field>
                );
              }}
            />
            <form.Field
              name={'cell_timeout'}
              children={field => {
                return (
                  <Field>
                    <div className={'flex flex-row gap-1.5'}>
                      <FieldLabel htmlFor={field.name}>Cell timeout</FieldLabel>
                      <Tooltip>
                        <TooltipTrigger>
                          <Info
                            className={'size-4 fill-primary text-background'}
                          />
                        </TooltipTrigger>
                        <TooltipContent>{CELL_TIMEOUT}</TooltipContent>
                      </Tooltip>
                    </div>
                    <Input
                      id={field.name}
                      name={field.name}
                      value={field.state.value ?? undefined}
                      type={'number'}
                      min={10}
                      onChange={e => field.handleChange(Number(e.target.value))}
                    />
                  </Field>
                );
              }}
            />
            <form.Field
              name={'allowed_file_patterns'}
              children={field => {
                return (
                  <Field>
                    <div className={'flex flex-row gap-1.5'}>
                      <FieldLabel htmlFor={field.name}>
                        Whitelist File Patterns
                      </FieldLabel>
                      <Tooltip>
                        <TooltipTrigger>
                          <Info
                            className={'size-4 fill-primary text-background'}
                          />
                        </TooltipTrigger>
                        <TooltipContent>
                          {WHITELIST_FILE_PATTERNS}
                        </TooltipContent>
                      </Tooltip>
                    </div>
                    <div className={'flex flex-row gap-3'}>
                      <Input
                        id={field.name}
                        name={field.name}
                        type={'text'}
                        value={whitelistPatternsInput}
                        onKeyDown={e => {
                          if (e.key === 'Enter') {
                            e.preventDefault();
                            e.stopPropagation();
                            handleAddAllowedFilePattern(field);
                          }
                        }}
                        onChange={e =>
                          setWhitelistPatternsInput(e.target.value)
                        }
                      />
                      <Button
                        id={field.name}
                        onClick={() => handleAddAllowedFilePattern(field)}
                        disabled={!whitelistPatternsInput}
                        type={'button'}
                      >
                        <CirclePlus /> Add
                      </Button>
                    </div>
                  </Field>
                );
              }}
            />
            {whitelist_patterns && (
              <div className={'flex flex-row gap-2'}>
                {whitelist_patterns.map(pattern => {
                  return (
                    <Badge key={pattern}>
                      {pattern}
                      <Button
                        className={'size-4'}
                        onClick={() => {
                          form.setFieldValue(
                            'allowed_file_patterns',
                            whitelist_patterns.filter(p => p !== pattern)
                          );
                        }}
                        type={'button'}
                      >
                        <XIcon className="size-3" aria-hidden="true" />
                      </Button>
                    </Badge>
                  );
                })}
              </div>
            )}
          </FieldGroup>
        </form>
        <DialogFooter>
          <Button
            type={props.assignment ? 'button' : 'submit'}
            form={props.assignment ? undefined : 'create-edit-assignment-form'}
            disabled={!form.state.isValid}
            onClick={props.assignment ? () => setConfirmOpen(true) : undefined}
          >
            {props.assignment ? 'Update' : 'Create'} assignment
          </Button>
          <DialogClose render={<Button variant={'outline'}>Cancel</Button>} />
          {!props.assignment && (
            <Field orientation={'horizontal'}>
              <Checkbox onCheckedChange={() => setCreateAnother(true)} />
              <FieldLabel>Create another</FieldLabel>
            </Field>
          )}
        </DialogFooter>
      </DialogContent>
      {confirmOpen && (
        <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
          <DialogContent className={'sm:max-w-1/4'}>
            <div className={'space-y-4'}>
              <FieldGroup className={'flex flex-row gap-2 items-center'}>
                <Checkbox
                  id={'recalc-scores'}
                  name={'recalc-scores'}
                  checked={recalcScoresConfirmed}
                  onCheckedChange={() =>
                    setRecalcScoresConfirmed(!recalcScoresConfirmed)
                  }
                ></Checkbox>
                <FieldLabel htmlFor={'recalc-scores'}>
                  Recalculate scores
                </FieldLabel>
                <Tooltip>
                  <TooltipTrigger>
                    <Info className={'size-4 fill-primary text-background'} />
                  </TooltipTrigger>
                  <TooltipContent>
                    Using this action will result in the <br />
                    recalculation of all submission scores based <br />
                    on the deadline/late submission settings.
                  </TooltipContent>
                </Tooltip>
              </FieldGroup>
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setConfirmOpen(false)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                onClick={() => {
                  setConfirmOpen(false);
                  form.handleSubmit();
                }}
              >
                Confirm
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
    </Dialog>
  );
};
