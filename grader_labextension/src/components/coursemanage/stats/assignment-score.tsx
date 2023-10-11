import React from 'react';
import { Box, Card, CardContent, CardHeader, Paper, Typography } from '@mui/material';
import {
  PolarAngleAxis,
  RadialBar,
  PieChart,
  ResponsiveContainer,
  Pie,
  Tooltip,
  TooltipProps
} from 'recharts';
import { GradeBook } from '../../../services/gradebook';
import {
  NameType,
  ValueType
} from 'recharts/types/component/DefaultTooltipContent';
import { useTheme } from '@mui/material/styles';

export interface IAssignmentScoreProps {
  gb: GradeBook;
}

const AssignmentScoreTooltip = ({
  active,
  payload,
  label
}: TooltipProps<ValueType, NameType>) => {
  if (active && payload && payload.length) {
    return (
      <Paper className="custom-tooltip">
        <Typography className="recharts-tooltip-label">
          <span>File: </span>
          <span style={{ color: payload[0].payload.fill }}>
            {payload[0].payload.notebook}
          </span>
        </Typography>
        <Typography className="recharts-tooltip-label">{`${payload[0].value} Point${
          payload[0].value === 1 ? '' : 's'
        }`}</Typography>
      </Paper>
    );
  }
  return null;
};

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

const getData = (gb: GradeBook): { notebook: string; points: number }[] => {
  if (gb === null) {
    return [];
  }
  return gb.getNotebooks().map((n, i) => {
    return {
      notebook: n,
      points: gb.getNotebookMaxPointsCells(n),
      fill: COLORS[i % COLORS.length]
    };
  });
};

export const AssignmentScore = (props: IAssignmentScoreProps) => {
  const [data, setData] = React.useState(
    [] as { notebook: string; points: number }[]
  );
  const darkMode = useTheme().palette.mode === 'dark';

  React.useEffect(() => {
    const d = getData(props.gb);
    setData(d);
  }, [props.gb]);

  return (
    <Card sx={{ height: 300, width: '100%' }}>
      <CardHeader
        sx={{ pb: 0 }}
        title={'Total Points'}
        subheader={'by notebooks'}
        subheaderTypographyProps={{ variant: 'caption' }}
      />
      <CardContent
        sx={{
          height: '70%'
        }}
      >
        <Box sx={{ height: '100%'}}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart cx="50%" cy="50%">
                <text fill={darkMode ? "#fff" : "#000"} fontSize={40} x={'50%'} y={'50%'} dy={12} textAnchor="middle">
                  {`${data.reduce((acc, v) => acc + v.points, 0).toFixed(2)}`}
                </text>
                <Tooltip content={<AssignmentScoreTooltip />} />
                <Pie
                  data={data}
                  dataKey="points"
                  nameKey="notebook"
                  innerRadius={'65%'}
                  outerRadius={'80%'}
                  paddingAngle={5}
                  stroke={darkMode ? '#555' : '#eee'}
                />
              </PieChart>
            </ResponsiveContainer>
        </Box>
      </CardContent>
    </Card>
  );
};
