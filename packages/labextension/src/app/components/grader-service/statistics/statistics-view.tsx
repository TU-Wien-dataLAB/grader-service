import React, { useMemo } from 'react';
import { Item, ItemContent, ItemDescription, ItemTitle } from '../../../shadcn-components/ui/item';
import { Star, User } from 'lucide-react';
import { ChartContainer, ChartTooltip, ChartTooltipContent, type ChartConfig } from '../../../shadcn-components/ui/chart';
import { CartesianGrid, Line, LineChart, XAxis, YAxis } from "recharts";
import { assignmentQuery } from '../../../../services/queries/assignments.queries';
import { useQuery } from '@tanstack/react-query';
import { getLectureUsers } from '../../../../services/lectures.service';
import { getSubmissions } from '../../../../services/submissions.service';

const chartConfig = {
  students: {
    label: "Students",
    color: "#E46E2E",
  },
} satisfies ChartConfig

const formatDate = (value: string) =>
  value.replace(/^\d{4}-(\d{2})-(\d{2})$/, '$2.$1.');

export const StatisticsView = ( {lectureId, assignmentId} : {lectureId: number, assignmentId: number}) => {

//fetch assignmnent data for total points
const { data: assignment } = useQuery(
    assignmentQuery(lectureId, assignmentId)
);

//fetch users for student count
const { data: users } = useQuery({
queryKey: ['users', lectureId],
queryFn: async () => getLectureUsers(lectureId, false)
});

//fetch submissions for submission count
const { data: submissions } = useQuery({
  queryKey: ['submissions-list', lectureId, assignmentId],
  queryFn: async () => getSubmissions(lectureId, assignmentId, 'none', true),
});
const submissionCount = useMemo(
  () => new Set((submissions ?? []).map((s) => s.user_id)).size,
  [submissions]
);

//fetch submission times for chart
const chartData = useMemo(() => {
  const studentsPerDay = new Map<string, Set<number>>();

  for (const s of submissions ?? []) {
    if (!s.submitted_at) continue;
    const date = s.submitted_at.slice(0, 10);

    let students = studentsPerDay.get(date);
    if (!students) {
      students = new Set<number>();
      studentsPerDay.set(date, students);
    }
    students.add(s.user_id);
  }
  if (studentsPerDay.size === 0) return [];

  const dates = [...studentsPerDay.keys()].sort();
  const end = new Date(dates[dates.length - 1] + 'T00:00:00Z');
  const result: { date: string; students: number }[] = [];

  for (let d = new Date(dates[0] + 'T00:00:00Z'); d <= end; d.setUTCDate(d.getUTCDate() + 1)) {
    const key = d.toISOString().slice(0, 10);
    result.push({ date: key, students: studentsPerDay.get(key)?.size ?? 0 });
  }
  return result;
}, [submissions]);


return (
    <div className={'flex flex-col items-start gap-4 self-stretch'}>
      <div className={'flex justify-between items-center self-stretch'}>
        <h2 className={'text-xl font-bold'}>Statistics</h2>
      </div>
      <div className={'grid grid-cols-2 auto-rows-fr gap-4 self-stretch'}>
        <Item className={'flex flex-row items-start gap-4 p-4 bg-card rounded-[2px]'}>
            <ItemContent>
                <ItemTitle className={'font-bold'}>
                    Submissions
                </ItemTitle>
                <ItemDescription className={'text-foreground'}>
                    How many students have already submitted:
                </ItemDescription>
                <div className={'flex flex-row items-center gap-2 mt-4'}>
                    <User strokeLinecap="butt" strokeLinejoin="miter" className={'text-foreground size-9 fill-foreground'} />
                    <div className={'text-3xl sm:text-4xl font-bold'}>{submissionCount}/{users.students?.length?.toString() ?? '0'}</div>
                </div>
            </ItemContent>
        </Item>
        <Item className={'flex flex-row items-start gap-4 p-4 bg-card rounded-[2px]'}>
            <ItemContent>
                <ItemTitle className={'font-bold'}>
                    Total Score
                </ItemTitle>
                <ItemDescription className={'text-foreground'}>
                    Total Points of this assignment:
                </ItemDescription>
                <div className={'flex flex-row items-center gap-2 mt-4'}>
                    <Star strokeLinecap="butt" strokeLinejoin="miter" className={'text-foreground size-9 fill-foreground'} />
                    <div className={'text-4xl font-bold'}>{assignment?.points}</div>
                </div>
            </ItemContent>
        </Item>
      </div>
      <Item className={'flex items-start p-4 bg-card rounded-[2px]'}>
        <ItemContent>
            <ItemTitle className={'font-bold'}>
                Submission times
            </ItemTitle>
            <ItemDescription className={'text-foreground'}>
                When did the students submit their work?
            </ItemDescription>
            <div className={'h-[200px] w-full'}>
                <ChartContainer  config={chartConfig} className={'aspect-auto h-full w-full bg-card rounded-[2px]'}>
                    <LineChart data={chartData}>
                        <CartesianGrid vertical={false}/>
                        <XAxis
                            dataKey="date"
                            tickLine={false}
                            tickMargin={10}
                            axisLine={false}
                            padding={{ left: 20, right: 20 }}
                            tickFormatter={(value) =>  value.replace(/^\d{4}-(\d{2})-(\d{2})$/, '$2.$1.')}
                        />
                        <YAxis
                            tickLine={false}
                            tickMargin={10}
                            axisLine={false}
                            allowDecimals={false}
                            domain={[0, 'auto']}
                        />
                        <ChartTooltip content={<ChartTooltipContent labelFormatter={(value) => formatDate(String(value))} indicator="line"/>}  />
                        <Line dataKey="students" type="linear" stroke="var(--color-students)" strokeWidth={2} dot={false} />
                    </LineChart>
                </ChartContainer>
                </div>
        </ItemContent>
      </Item>
      
    </div>
  );
};