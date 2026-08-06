import { useQuery } from '@tanstack/react-query';
import { activeInstructorLecturesQuery } from '../../../services/queries/lectures.queries';
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar
} from '../../shadcn-components/ui/sidebar';
import { Link, useLocation } from 'react-router';
import {
  ChevronLeft,
  ChevronRight,
  Eye,
  GraduationCap,
  Pencil
} from 'lucide-react';
import { Button } from '../../shadcn-components/ui/button';
import React, { useMemo } from 'react';
import { Separator } from '../../shadcn-components/ui/separator';
import {
  Collapsible,
  CollapsibleTrigger
} from '../../shadcn-components/ui/collapsible';
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '../../shadcn-components/ui/select';
import {
  ToggleGroup,
  ToggleGroupItem
} from '../../shadcn-components/ui/toggle-group';
import { LogoWithText } from '../../../assets/logo-with-text';
import { Logo } from '../../../assets/logo';

export const GlobalSidebar = () => {
  const { data: fetchedLectures } = useQuery(activeInstructorLecturesQuery());
  const location = useLocation();
  const lectures = useMemo(() => {
    return fetchedLectures?.map(lecture => ({
      ...lecture,
      isActive: location.pathname === `/lectures/${lecture.id}`
    }));
  }, [fetchedLectures, location.pathname]);

  const { state, toggleSidebar } = useSidebar();

  const languages = [
    {
      label: state === 'collapsed' ? 'EN' : 'English - EN',
      value: 'en'
    },
    { label: state === 'collapsed' ? 'DE' : 'Deustch - DE', value: 'de' }
  ];

  return (
    <Sidebar collapsible={'icon'} className={'h-full'}>
      <SidebarHeader className={'h-13.5 pl-0'}>
        <Link
          to={'/'}
          className={`flex px-2 h-full w-full ${
            state === 'collapsed' ? 'justify-center' : 'justify-start'
          } items-center`}
        >
          {state === 'collapsed' ? (
            <Logo className={'size-20'}></Logo>
          ) : (
            <LogoWithText className={'size-20'} />
          )}
        </Link>
      </SidebarHeader>
      <Separator className={'w-full'} />
      <SidebarContent>
        <SidebarGroup className={'p-0'}>
          <SidebarMenu>
            {lectures?.map(lecture => (
              <Collapsible key={lecture.id} className={'h-17.5'}>
                <SidebarMenuItem
                  key={lecture.id}
                  className={`${
                    lecture.isActive
                      ? 'bg-[#FAE2D5] dark:bg-[#E46E2E]'
                      : 'bg-input'
                  } h-17`}
                >
                  <CollapsibleTrigger
                    render={
                      <SidebarMenuButton
                        className={`${
                          state === 'collapsed'
                            ? 'justify-center'
                            : 'justify-start'
                        } h-full`}
                        tooltip={lecture.name}
                      />
                    }
                  >
                    <Link
                      to={`/lectures/${lecture.id}`}
                      className="overflow-hidden"
                    >
                      <div
                        className={`${
                          state === 'collapsed' ? 'flex-col' : 'flex-row'
                        } flex gap-2`}
                      >
                        <GraduationCap className="size-8 self-center" />
                        <div className="flex flex-col overflow-hidden">
                          {state === 'expanded' && (
                            <div className="text-lg font-bold truncate">
                              {lecture.name}
                            </div>
                          )}
                          <div className="text-sm">{lecture.code}</div>
                        </div>
                      </div>
                    </Link>
                  </CollapsibleTrigger>
                </SidebarMenuItem>
                <Separator className={'w-full'} />
              </Collapsible>
            ))}
          </SidebarMenu>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter className={'items-center'}>
        <Select defaultValue={'en'} items={languages}>
          <SelectTrigger className={'w-full'}>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectGroup>
              {languages.map(({ label, value }) => (
                <SelectItem key={value} value={value}>
                  {label}
                </SelectItem>
              ))}
            </SelectGroup>
          </SelectContent>
        </Select>
        <ToggleGroup type={'single'} className={'rounded-xs w-fit'}>
          {state === 'collapsed' ? (
            <>
              <ToggleGroupItem value={'instructor'}>
                <Pencil className={'size-4'} />
              </ToggleGroupItem>
              <ToggleGroupItem value={'student'} variant={'outline'}>
                <Eye className={'size-4'} />
              </ToggleGroupItem>
            </>
          ) : (
            <>
              <ToggleGroupItem value={'instructor'} variant={'default'}>
                Instructor View
              </ToggleGroupItem>
              <ToggleGroupItem value={'student'} variant={'outline'}>
                Student View
              </ToggleGroupItem>
            </>
          )}
        </ToggleGroup>
        <Separator className={'w-full'} />
        <Button
          variant="link"
          onClick={() => toggleSidebar()}
          className="ml-auto"
        >
          {state === 'collapsed' ? (
            <ChevronRight className="size-4" />
          ) : (
            <>
              Collapse Sidebar <ChevronLeft className="size-4" />
            </>
          )}
        </Button>
      </SidebarFooter>
    </Sidebar>
  );
};
