import React, {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState
} from 'react';
import { useParams } from 'react-router';
import { useQuery } from '@tanstack/react-query';
import { Button } from '../../shadcn-components/ui/button';
import { SearchField } from '../../components/ui/search';
import { FilterAssignmentsButton } from '../../components/ui/filter-button';
import { SortButton } from '../../components/ui/sort-button';
import { AssignmentDetail } from '../../../model/assignmentDetail';
import { AssignmentGroup } from '../../components/grader-service/assignments/assignment-group';
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import withScrolling from 'react-dnd-scrolling';
import { AssignmentSettings } from '../../../model/assignmentSettings';
import AutogradeTypeEnum = AssignmentSettings.AutogradeTypeEnum;
import { Assignment } from '../../../model/assignment';
import StatusEnum = Assignment.StatusEnum;
import { EllipsisVertical, X } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger
} from '../../shadcn-components/ui/dropdown-menu';
import { AssignmentSettingsDialog } from '../../components/grader-service/assignments/assignment-settings-dialog';
import { ExportGradesDialog } from '../../components/grader-service/assignments/export-grades-dialog';
import { lectureQuery } from '../../../services/queries/lectures.queries';
import { assignmentsQuery } from '../../../services/queries/assignments.queries';
import { useMutationStatus } from '../../../widget';
import { SuccessBanner } from '../../components/ui/success-banner';
import { ErrorBanner } from '../../components/ui/error-banner';
import { Badge } from '../../shadcn-components/ui/badge';

export interface IAssignmentChecked {
  assignment: AssignmentDetail;
  checked: boolean;
}

interface IGroupsContextValue {
  groups: string[];
  customGroups: string[];
  addCustomGroup: (group: string) => void;
}
// we need context for groups to be able to choose from or add new groups in
// deeply nested children components (e.g. AssignmentActions)
const GroupsContext = createContext<IGroupsContextValue | null>(null);

export function GroupsProvider({
  assignments,
  children
}: {
  assignments: AssignmentDetail[];
  children: React.ReactNode;
}) {
  const [customGroups, setCustomGroups] = useState<string[]>([]);

  const groups = useMemo(() => {
    if (!assignments) {
      return [];
    }
    const fromAssignments = [
      ...new Set(assignments.map(a => a.settings.group))
    ].filter(Boolean);
    return [...new Set([...fromAssignments, ...customGroups])].sort((a, b) =>
      a.localeCompare(b)
    );
  }, [assignments, customGroups]);

  const addCustomGroup = useCallback((group: string) => {
    setCustomGroups(prev => [...new Set([...prev, group])]);
  }, []);

  return (
    <GroupsContext.Provider value={{ groups, customGroups, addCustomGroup }}>
      {children}
    </GroupsContext.Provider>
  );
}
export const useGroups = () => {
  const ctx = useContext(GroupsContext);
  if (!ctx) {
    throw new Error('useGroups must be used within GroupsProvider');
  }
  return ctx;
};

const STATIC_FILTERS = [
  {
    key: 'Grading method',
    value: AutogradeTypeEnum.Auto,
    label: 'Automatic'
  },
  {
    key: 'Grading method',
    value: AutogradeTypeEnum.Unassisted,
    label: 'Manual'
  },
  {
    key: 'Grading method',
    value: AutogradeTypeEnum.FullAuto,
    label: 'Fully automatic'
  },
  { key: 'Deadline', value: 'Overdue', label: 'Overdue' },
  { key: 'Deadline', value: 'Upcoming', label: 'Upcoming' },
  { key: 'Deadline', value: 'No Deadline', label: 'No Deadline' },
  { key: 'Status', value: StatusEnum.Created, label: 'Not Released' },
  { key: 'Status', value: StatusEnum.Released, label: 'Released' },
  { key: 'Status', value: StatusEnum.Complete, label: 'Completed' }
];

const ScrollingComponent = withScrolling('div');

export const Lecture = () => {
  const params = useParams();
  const lectureId = Number(params.id);

  const { data: lecture, isPending: isPendingLecture } = useQuery(
    lectureQuery(lectureId)
  );

  const {
    data: assignments,
    isPending: isPendingAssignments,
    isRefetching: isRefetchingAssignments
  } = useQuery(assignmentsQuery(lectureId));

  // filtering logic
  const [sortBy, setSortBy] = useState({ key: '', dir: '' });
  const [searchQuery, setSearchQuery] = useState('');

  // TODO: refactor
  const allFilters = useMemo(() => {
    if (isPendingAssignments) {
      return;
    }
    // extract all groups from assignments
    const dynamicGroups = [...new Set(assignments.map(a => a.settings.group))]
      .filter(Boolean)
      .map(value => ({ key: 'Group', value, label: value }));
    // check if there are assignments with no group assigned
    const ungroupedAssignmentsExist = assignments.some(
      a => a.settings.group === '' || !a.settings.group
    );
    return [
      ...STATIC_FILTERS,
      ungroupedAssignmentsExist && {
        key: 'Group',
        value: 'Ungrouped assignments',
        label: 'Ungrouped assignments'
      },
      ...(dynamicGroups ?? [])
    ];
  }, [assignments, isPendingAssignments]);

  // Group filters by key for rendering
  const filterGroups = useMemo(() => {
    if (allFilters) {
      return allFilters.reduce<Record<string, typeof STATIC_FILTERS>>(
        (acc, filter) => {
          (acc[filter.key] ??= []).push(filter);
          return acc;
        },
        {}
      );
    }
  }, [allFilters]);

  // active filters are set as key:value
  const [activeFilters, setActiveFilters] = useState(new Set<string>());
  // used for checking/unchecking a checkbox
  const toggle = (key: string, value: string, label: string) => {
    const id = `${key}:${value}:${label}`;
    setActiveFilters(prev => {
      const next = new Set(prev);
      // eslint-disable-next-line @typescript-eslint/no-unused-expressions
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  // search, filter and sort function
  const filteredAssignments = useMemo(() => {
    let result;

    if (isPendingAssignments) {
      return [];
    }

    result = [...assignments];
    if (searchQuery) {
      result = result.filter(a =>
        a.name.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    if (activeFilters) {
      const currentDate = new Date();
      const activeGroups: Record<string, string[]> = {};
      for (const id of activeFilters) {
        const [key, value] = id.split(':');
        (activeGroups[key] ??= []).push(value);
      }

      if (activeGroups['Status']) {
        result = result.filter(a => activeGroups['Status'].includes(a.status));
      }

      if (activeGroups['Grading Mode']) {
        result = result.filter(a =>
          activeGroups['Grading Mode'].includes(a.settings.autograde_type)
        );
      }

      if (activeGroups['Deadline']) {
        result = result.filter(a => {
          if (activeGroups['Deadline'].includes('No Deadline')) {
            return !a.settings.deadline;
          }
          const deadline = a.settings.deadline
            ? new Date(a.settings.deadline)
            : undefined;
          return activeGroups['Deadline'].some(v =>
            deadline && v === 'Overdue'
              ? deadline < currentDate
              : deadline > currentDate
          );
        });
      }

      if (activeGroups['Group']) {
        result = result.filter(
          a =>
            activeGroups['Group'].includes(a.settings.group) ||
            (activeGroups['Group'].includes('Ungrouped assignments') &&
              !a.settings.group)
        );
      }
    }
    if (sortBy) {
      result = result.sort((a, b) => {
        const modifier = sortBy.dir === 'asc' ? 1 : -1;
        if (sortBy.key === 'name') {
          return (a.name ?? '').localeCompare(b.name ?? '') * modifier;
        }
        if (sortBy.key === 'date') {
          return (a.id - b.id) * modifier;
        }
        return 0;
      });
    }

    return result;
  }, [
    assignments,
    isPendingAssignments,
    isRefetchingAssignments,
    searchQuery,
    sortBy,
    activeFilters
  ]);

  // split assignments based on their group
  const groupsDict = useMemo(() => {
    const dict: Record<string, IAssignmentChecked[]> = {};
    if (!isPendingAssignments) {
      filteredAssignments.forEach(assignment => {
        const group = assignment.settings.group;
        const key =
          group !== null && group !== '' ? group : 'ungrouped assignments';
        if (!dict[key]) {
          dict[key] = [];
        }
        dict[key].push({ assignment, checked: false });
      });
    }

    // ensure "ungrouped assignments" appears first, if present
    if (dict['ungrouped assignments']) {
      const { 'ungrouped assignments': ungrouped, ...rest } = dict;
      return { 'ungrouped assignments': ungrouped, ...rest };
    }

    return dict;
  }, [filteredAssignments]);
  const [openAssignmentSettings, setOpenAssignmentSettings] = useState(false);
  const [openExportGradesDialog, setOpenExportGradesDialog] = useState(false);

  const { status } = useMutationStatus();
  return (
    <GroupsProvider assignments={assignments}>
      <div
        className={
          'flex flex-col bg-background items-start p-6 gap-6 self-stretch w-full h-full overflow-hidden'
        }
      >
        <div
          className={
            'flex flex-row sticky justify-between items-center self-stretch'
          }
        >
          {!isPendingLecture && (
            <div className={'flex flex-col gap-1 items-start'}>
              <h1 className={'text-2xl font-bold'}>{lecture.name}</h1>
              <h3 className={'text-base font-bold'}>{lecture.code}</h3>
            </div>
          )}
          <div className={'ml-auto flex items-start'}>
            <Button
              onClick={() => setOpenAssignmentSettings(true)}
              variant={'outline'}
            >
              New assignment
            </Button>
            <DropdownMenu modal={false}>
              <DropdownMenuTrigger>
                <Button variant={'link'} className={'p-2'}>
                  <EllipsisVertical className={'size-5'}></EllipsisVertical>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuItem
                  onClick={() => setOpenExportGradesDialog(true)}
                >
                  Export grades
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
        {status.status === 'success' && (
          <SuccessBanner message={status.message} />
        )}
        {status.status === 'error' && <ErrorBanner message={status.message} />}
        <div className={'flex justify-between items-center self-stretch'}>
          <SearchField
            placeholder={'Search for assignment'}
            recentSearchesKey={'assignment-search-history'}
            searchQuery={searchQuery}
            setSearchQuery={setSearchQuery}
          />
          <div className={'flex flex-row ml-auto gap-3'}>
            <FilterAssignmentsButton
              filterGroups={filterGroups}
              activeFilters={activeFilters}
              toggle={toggle}
            />
            <SortButton sortBy={sortBy} setSortBy={setSortBy} />
          </div>
          {openAssignmentSettings && (
            <AssignmentSettingsDialog
              lectureId={lectureId}
              openDialog={openAssignmentSettings}
              setOpenDialog={setOpenAssignmentSettings}
            />
          )}
          {openExportGradesDialog && (
            <ExportGradesDialog
              lecture={lecture}
              isOpen={openExportGradesDialog}
              setIsOpen={setOpenExportGradesDialog}
            />
          )}
        </div>
        {activeFilters.size > 0 && (
          <div className={'flex flex-row gap-4 items-start'}>
            {Array.from(activeFilters).map(id => {
              const [key, value, label] = id.split(':');
              return (
                <div
                  className={
                    'flex items-center gap-0.5 rounded-xs border border-muted-foreground'
                  }
                >
                  <Badge variant={'secondary'} className={'p-0 pl-2'}>
                    <span className={'font-bold'}>{key}</span>: {label}
                    <Button
                      variant={'link'}
                      onClick={() => toggle(key, value, label)}
                    >
                      <X className={'size-4'} aria-label={'Remove filter'} />
                    </Button>
                  </Badge>
                </div>
              );
            })}
            <Button
              variant={'link'}
              aria-label={'Reset filters'}
              onClick={() => setActiveFilters(new Set())}
            >
              Reset filter
            </Button>
          </div>
        )}
        {filteredAssignments && filteredAssignments.length > 0 ? (
          <DndProvider backend={HTML5Backend}>
            <ScrollingComponent className={'overflow-y-auto h-full w-full'}>
              {Object.entries(groupsDict).map(
                ([groupKey, groupAssignments]) => (
                  <AssignmentGroup
                    key={groupKey}
                    lectureId={lectureId}
                    assignmentGroup={groupKey}
                    groupAssignments={groupAssignments}
                    allAssignments={filteredAssignments}
                  />
                )
              )}
            </ScrollingComponent>
          </DndProvider>
        ) : (
          <div className={'flex flex-col items-center justify-center h-full'}>
            <p className={'text-3xl'}>No assignments yet...</p>
            <Button onClick={() => setOpenAssignmentSettings(true)}>
              Create first assignment
            </Button>
          </div>
        )}
      </div>
    </GroupsProvider>
  );
};
