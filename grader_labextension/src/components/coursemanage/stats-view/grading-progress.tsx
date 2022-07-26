import {filterUserSubmissions, IStatsProps} from "./stats";
import React from "react";
import {Submission} from "../../../model/submission";
import {Card, CardContent, CardHeader} from "@mui/material";
import {Legend, PolarAngleAxis, RadialBar, RadialBarChart, ResponsiveContainer} from "recharts";

interface GradingProgressData {
  auto: number,
  manual: number,
  feedback: number
}

const getData = (
  submissions: Submission[],
  users: { students: string[]; tutors: string[]; instructors: string[] }
): GradingProgressData => {
  const subs = filterUserSubmissions(submissions, users.instructors.concat(users.tutors));
  let totalCounts = subs.reduce((acc, v) => {
    if (v.auto_status === "automatically_graded") acc.a++;
    if (v.manual_status === "manually_graded") acc.m++;
    if (v.feedback_available) acc.f++;
    return acc
  }, {a: 0, m: 0, f: 0})

  // return {auto: 0.7, manual: 0.5, feedback: 0.2}

  if (subs.length === 0) {
    return {auto: 0, manual: 0, feedback: 0}
  }

  // we assume latest submissions only so subs only contains unique users
  return {
    auto: totalCounts.a / subs.length,
    manual: totalCounts.m / subs.length,
    feedback: totalCounts.f / subs.length
  }
}


export const GradingProgress = (props: IStatsProps) => {
  const [data, setData] = React.useState([]);

  React.useEffect(() => {
    const d = getData(props.latestSubmissions, props.users);
    const a = [
      {name: "Feedback", value: d.feedback, fill: '#00C49F'},
      {name: "Manual", value: d.manual, fill: '#0088FE'},
      {name: "Auto", value: d.auto, fill: '#FFBB28'},
    ];
    setData(a);
  }, [props.latestSubmissions, props.users])

  return (
    <Card sx={{height: 300, width: "100%"}}>
      <CardHeader sx={{pb: 0}} title={"Grading Status"} subheader={"as % of latest student submissions"}
                  subheaderTypographyProps={{variant: "caption"}}/>
      <CardContent
        sx={{height: "70%", width: "100%", display: "flex", justifyContent: "center", alignItems: "center", p: 0.5}}>
        <ResponsiveContainer width="100%" height="100%">
          <RadialBarChart cx="50%" cy="50%" innerRadius="30%" outerRadius="90%" barSize={15} data={data}>
            <PolarAngleAxis type="number" domain={[0, 1]} angleAxisId={0} tick={false}/>
            <RadialBar background dataKey='value' angleAxisId={0}/>
            <Legend layout="horizontal" verticalAlign="bottom" align="center"/>
          </RadialBarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>

  )
}