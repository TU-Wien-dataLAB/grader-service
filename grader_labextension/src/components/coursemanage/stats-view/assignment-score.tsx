import {IStatsProps} from "./stats";
import React from "react";
import {Card, CardContent, CardHeader} from "@mui/material";
import {PolarAngleAxis, RadialBar, PieChart, ResponsiveContainer, Pie, Tooltip} from "recharts";
import {GradeBook} from "../../../services/gradebook";

export interface IAssignmentScoreProps {
  gb: GradeBook
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

const getData = (gb: GradeBook): { notebook: string, points: number }[] => {
  if (gb === null) return [];
  return gb.getNotebooks().map((n, i) => {
    return {notebook: n, points: gb.getNotebookMaxPointsCells(n), fill: COLORS[i % COLORS.length]}
  })
}

export const AssignmentScore = (props: IAssignmentScoreProps) => {
  const [data, setData] = React.useState([] as { notebook: string, points: number }[]);

  React.useEffect(() => {
    const d = getData(props.gb);
    console.log(d);
    setData(d);
  }, [props]);

  return (
    <Card sx={{height: 300, width: "100%"}}>
      <CardHeader sx={{pb: 0}} title={"Total Points"} subheader={"by notebooks"}
                  subheaderTypographyProps={{variant: "caption"}}/>
      <CardContent
        sx={{height: "70%", width: "100%", display: "flex", justifyContent: "center", alignItems: "center", p: 0.5}}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart cx="50%" cy="50%">
            <text fontSize={40} x={"50%"} y={"50%"} dy={12} textAnchor="middle">
              {`${data.reduce((acc, v) => acc + v.points, 0).toFixed(1)}`}
            </text>
            <Tooltip/>
            <Pie data={data} dataKey='points' nameKey='notebook' innerRadius={"65%"} outerRadius={"80%"}
                 paddingAngle={5}/>
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>

  )
}