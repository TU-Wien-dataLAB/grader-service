import React, { useEffect } from 'react';
import { Header } from '../../components/ui/header';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../shadcn-components/ui/tabs';
import { UpcomingAssignments } from '../../components/grader-service/assignments/upcoming_assignments';
import { lectureBasePath, openInFileBrowser } from '../../../services/local-file.service';
import { Courses } from '../../components/grader-service/lectures/courses';


export const Dashboard = () => {
    useEffect(() => {
      openInFileBrowser(`${lectureBasePath}`);
    });

  return (
    <div
      className={'flex h-full flex-col w-full overflow-hidden bg-background'}
      id={'lecture-view'}
    >
    <Header />
    <Tabs defaultValue="upcoming assignments" className="m-6 flex flex-col flex-1 min-h-0">
        <TabsList className="border-b border-border w-full justify-start p-0 rounded-none bg-transparent">
            <TabsTrigger value="upcoming assignments" className="-mb-0.5 flex-none px-4 py-1.5 text-primary border-b-2 border-transparent aria-selected:border-b-primary rounded-none aria-selected:bg-card hover:text-primary/80">Upcoming Assignments</TabsTrigger>
            <TabsTrigger value="courses" className="-mb-0.5 flex-none text-primary border-b-2 border-transparent aria-selected:border-b-primary rounded-none aria-selected:bg-card hover:text-primary/80">Courses</TabsTrigger>
        </TabsList>
        <TabsContent value="upcoming assignments" className="flex-1 min-h-0 overflow-hidden">
            <UpcomingAssignments />
        </TabsContent>
        <TabsContent value="courses" className="flex-1 min-h-0 overflow-hidden">
            <Courses />
        </TabsContent>
    </Tabs>
      
    </div>
    
  );
};
