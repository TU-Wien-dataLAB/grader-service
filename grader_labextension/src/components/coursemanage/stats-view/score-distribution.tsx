import {IStatsProps} from "./stats";
import React from "react";
import {Submission} from "../../../model/submission";
import {Assignment} from "../../../model/assignment";
import {Button, Card, CardContent, CardHeader, TextField, Typography} from "@mui/material";
import {Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis} from "recharts";
import moment from "moment";

interface Bucket {
  start: number,
  end: number,
  count: number,
}

const binData = (data: number[], min: number, max: number, numBuckets: number): Bucket[] => {
  const bucketSize = (max - min) / numBuckets;
  let currBucket = min;
  const buckets = new Array<number>(numBuckets).fill(0).map(v => {
    return {start: currBucket, end: currBucket += bucketSize, count: v} as Bucket
  });
  for (const v of data) {
    let bucketIndex = Math.floor((v - min) / bucketSize);
    bucketIndex = Math.min(bucketIndex, numBuckets - 1);
    buckets[bucketIndex].count++;
  }

  return buckets;
}

const getData = (
  submissions: Submission[],
  assignment: Assignment,
  numBuckets: number
): { name: string, count: number }[] => {
  const getBaseLog = (x: number, y: number) => Math.log(y) / Math.log(x);
  const decimalPlaces = -Math.floor(getBaseLog(10, assignment.points / numBuckets)) + 1
  const data = submissions.map(s => (s.score || 0));
  const buckets = binData(data, 0, assignment.points, numBuckets);
  return buckets.map(v => {
    return {name: `${v.start.toFixed(decimalPlaces)}-${v.end.toFixed(decimalPlaces)}`, count: v.count}
  })
}

export const ScoreDistribution = (props: IStatsProps) => {
  const [data, setData] = React.useState([] as { name: string, count: number }[]);
  const startBuckets = 10;

  React.useEffect(() => {
    const d = getData(props.latestSubmissions, props.assignment, startBuckets);
    console.log(d);
    setData(d);
  }, [])

  return (
    <Card sx={{height: 300, width: "100%"}}>
      <CardHeader
        title={"Distribution of Scores"}
        action={<TextField
          id="outlined-number"
          size="small"
          margin="dense"
          InputProps={{inputProps: {min: 1, max: Math.max(Math.floor(props.assignment.points), 20)}}}
          defaultValue={startBuckets}
          onChange={v => setData(getData(props.latestSubmissions, props.assignment, +v.target.value))}
          label="Buckets"
          type="number"
          InputLabelProps={{
            shrink: true,
          }}
        />}/>
      <CardContent
        sx={{height: "70%", width: "100%", display: "flex", justifyContent: "center", alignItems: "center", p: 0.5}}>
        {(data.reduce((acc, v) => acc + v.count, 0) === 0)
          ? <Typography color={"text.secondary"}>No Data Available</Typography>
          : <ResponsiveContainer width="100%" height="100%">
            <BarChart
              height={150}
              width={250}
              data={data}
              margin={{
                top: 5,
                right: 30,
                left: 0,
                bottom: 5,
              }}
              barGap={0}
              barCategoryGap={0}
            >
              <XAxis dataKey="name"/>
              <YAxis dataKey="count"/>
              <Tooltip/>
              <Bar dataKey="count" fill={"#8884d8"}/>
            </BarChart>
          </ResponsiveContainer>
        }
      </CardContent>
    </Card>
  )
}