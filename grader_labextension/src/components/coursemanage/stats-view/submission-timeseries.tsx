import * as React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  TooltipProps, Brush
} from 'recharts';
import {Card, CardContent, CardHeader, Typography} from "@mui/material";
import {IStatsProps} from "./stats";
import moment from "moment";
import {Submission} from "../../../model/submission";
import {NameType, ValueType} from "recharts/types/component/DefaultTooltipContent";

const CustomTooltip = ({active, payload, label}: TooltipProps<ValueType, NameType>) => {
  if (active && payload && payload.length) {
    return (
      <div className="custom-tooltip">
        <p className="label">{`${payload[0].value} Submission${payload[0].value === 1 ? '' : 's'}`}</p>
      </div>
    );
  }

  return null;
};

const getData = (submissions: Submission[]): { time: number, n: number }[] => {
  if (submissions.length === 0) return [];
  const map = submissions
    .map(s => moment(s.submitted_at).startOf("day").valueOf())
    .reduce((acc, v) => {
      const c = acc.has(v) ? acc.get(v) : 0;
      acc.set(v, c + 1);
      return acc;
    }, new Map<number, number>())

  const dates: Array<number> = [];
  let currDate = moment(Math.min(...map.keys())).subtract(1, 'days');
  let lastDate = moment();

  while (currDate.add(1, 'days').diff(lastDate) < 0) {
    dates.push(currDate.valueOf());
  }
  return dates.map(d => {
    if (map.has(d)) {
      return {time: d, n: map.get(d)}
    } else {
      return {time: d, n: 0}
    }
  });
}

export const SubmissionTimeSeries = (props: IStatsProps) => {
  const [data, setData] = React.useState([] as { time: number, n: number }[]);

  React.useEffect(() => {
    const d = getData(props.allSubmissions);
    console.log(d);
    setData(d);
  }, [])

  return (
    <Card sx={{height: 300, width: "100%"}}>
      <CardHeader title={"Submissions"}/>
      <CardContent
        sx={{height: "70%", width: "100%", display: "flex", justifyContent: "center", alignItems: "center", p: 0.5}}>
        {(data.length === 0)
          ? <Typography color={"text.secondary"}>No Data Available</Typography>
          : <ResponsiveContainer width="100%" height="100%">
            <LineChart
              height={150}
              width={250}
              data={data}
              margin={{
                top: 5,
                right: 30,
                left: 0,
                bottom: 5,
              }}
            >
              <XAxis dataKey="time" tickFormatter={(unixTime) => moment(unixTime).format('DD MMM')}/>
              <YAxis dataKey="n"/>
              <Tooltip label={"Number of Submissions"} content={<CustomTooltip/>}/>
              <Line type="monotone" dataKey="n" stroke="#8884d8" activeDot={{r: 8}} strokeWidth={4}/>
              <Brush height={10}/>
            </LineChart>
          </ResponsiveContainer>
        }
      </CardContent>
    </Card>

  )
}