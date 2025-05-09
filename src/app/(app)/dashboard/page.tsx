
'use client';

import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { DataCard } from "@/components/shared/data-card";
import { dashboardSummaryMetrics, mockAttendance, mockLeaveRequests } from "@/lib/data";
import { BarChart as LucideBarChart, CalendarDays, CheckCircle, Users, CalendarX } from "lucide-react";
import Image from "next/image";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { addDays, format, formatISO, parseISO, startOfDay } from 'date-fns';
import type { ChartConfig } from "@/components/ui/chart";
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import dynamic from 'next/dynamic';

// Dynamically import Recharts components
const ResponsiveContainer = dynamic(() => import('recharts').then(mod => mod.ResponsiveContainer), { ssr: false, loading: () => <p className="text-center text-muted-foreground py-8">Loading chart...</p> });
const RechartsBarChartPrimitive = dynamic(() => import('recharts').then(mod => mod.BarChart), { ssr: false, loading: () => <p className="text-center text-muted-foreground py-8">Loading chart...</p> });
const CartesianGrid = dynamic(() => import('recharts').then(mod => mod.CartesianGrid), { ssr: false });
const XAxis = dynamic(() => import('recharts').then(mod => mod.XAxis), { ssr: false });
const YAxis = dynamic(() => import('recharts').then(mod => mod.YAxis), { ssr: false });
const Bar = dynamic(() => import('recharts').then(mod => mod.Bar), { ssr: false });


const upcomingAbsencesChartConfig = {
  absentCount: { label: "Absent Employees", color: "hsl(var(--chart-4))" }, // Using chart-4 for variety
} satisfies ChartConfig;

export default function DashboardPage() {
  const [isClient, setIsClient] = React.useState(false);

  React.useEffect(() => {
    setIsClient(true);
  }, []);

  const today = new Date().toISOString().split('T')[0];
  const recentAttendance = mockAttendance.filter(a => a.date === today).slice(0, 5);
  const upcomingLeaves = mockLeaveRequests.filter(lr => lr.status === 'Approved' && new Date(lr.startDate) >= new Date()).slice(0,3);

  const upcomingAbsencesData = React.useMemo(() => {
    if (!isClient) return []; // Prevent calculation on server or before client hydration
    
    const currentDay = startOfDay(new Date());
    const data = [];
    for (let i = 0; i < 7; i++) {
      const targetDate = addDays(currentDay, i);
      const dateStr = formatISO(targetDate, { representation: 'date' });
      
      let absentCount = 0;
      mockLeaveRequests.forEach(lr => {
        if (lr.status === 'Approved') {
          const startDate = startOfDay(parseISO(lr.startDate));
          const endDate = startOfDay(parseISO(lr.endDate));
          if (targetDate >= startDate && targetDate <= endDate) {
            absentCount++;
          }
        }
      });
      
      data.push({
        date: format(targetDate, 'MMM dd'),
        fullDate: dateStr,
        absentCount: absentCount,
      });
    }
    return data;
  }, [isClient]);


  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold tracking-tight text-foreground">Dashboard</h1>
      
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {dashboardSummaryMetrics.map((metric, index) => (
          <DataCard 
            key={metric.label + index}
            title={metric.label}
            value={metric.value.toString()}
            icon={metric.icon}
            description={metric.description || metric.change}
          />
        ))}
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CalendarDays className="h-5 w-5 text-primary" />
              Today's Attendance Snapshot
            </CardTitle>
            <CardDescription>A quick look at who is in today.</CardDescription>
          </CardHeader>
          <CardContent>
            {recentAttendance.length > 0 ? (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Employee</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {recentAttendance.map((att) => (
                    <TableRow key={att.id}>
                      <TableCell className="font-medium">{att.employeeName}</TableCell>
                      <TableCell>
                        <Badge variant={att.status === 'Present' || att.status === 'Late' ? 'default' : 'secondary'}
                               className={cn(
                                 att.status === 'Present' && 'bg-green-500/20 text-green-700 dark:bg-green-500/30 dark:text-green-400 border-green-500/30',
                                 att.status === 'Late' && 'bg-yellow-500/20 text-yellow-700 dark:bg-yellow-500/30 dark:text-yellow-400 border-yellow-500/30',
                                 att.status === 'On Leave' && 'bg-blue-500/20 text-blue-700 dark:bg-blue-500/30 dark:text-blue-400 border-blue-500/30',
                                 att.status === 'Absent' && 'bg-red-500/20 text-red-700 dark:bg-red-500/30 dark:text-red-400 border-red-500/30'
                               )}
                        >
                          {att.status}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <p className="text-sm text-muted-foreground">No attendance records for today yet.</p>
            )}
          </CardContent>
        </Card>

        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-primary" />
              Upcoming Approved Leaves
            </CardTitle>
            <CardDescription>Employees with approved time off soon.</CardDescription>
          </CardHeader>
          <CardContent>
             {upcomingLeaves.length > 0 ? (
              <ul className="space-y-3">
                {upcomingLeaves.map(leave => (
                  <li key={leave.id} className="flex items-center justify-between p-3 bg-muted/50 rounded-md">
                    <div>
                      <p className="font-semibold">{leave.employeeName}</p>
                      <p className="text-xs text-muted-foreground">{leave.leaveType} Leave</p>
                    </div>
                    <p className="text-sm">{new Date(leave.startDate).toLocaleDateString()} - {new Date(leave.endDate).toLocaleDateString()}</p>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-muted-foreground">No upcoming approved leaves.</p>
            )}
          </CardContent>
        </Card>

        <Card className="shadow-lg md:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CalendarX className="h-5 w-5 text-primary" />
              Upcoming Absences (Next 7 Days)
            </CardTitle>
            <CardDescription>Number of employees scheduled to be absent due to approved leave.</CardDescription>
          </CardHeader>
          <CardContent>
            {isClient && upcomingAbsencesData.length > 0 ? (
              <ChartContainer config={upcomingAbsencesChartConfig} className="h-[300px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <RechartsBarChartPrimitive data={upcomingAbsencesData} margin={{ top: 5, right: 20, left: -20, bottom: 5 }}>
                    <CartesianGrid vertical={false} strokeDasharray="3 3" />
                    <XAxis
                      dataKey="date"
                      tickLine={false}
                      axisLine={false}
                      tickMargin={8}
                      fontSize={12}
                    />
                    <YAxis allowDecimals={false} tickLine={false} axisLine={false} tickMargin={8} fontSize={12} />
                    <ChartTooltip
                      cursor={false}
                      content={<ChartTooltipContent indicator="dot" />}
                    />
                    <Bar dataKey="absentCount" fill="var(--color-absentCount)" radius={4} />
                  </RechartsBarChartPrimitive>
                </ResponsiveContainer>
              </ChartContainer>
            ) : (
              <div className="h-[300px] w-full flex items-center justify-center">
                <p className="text-muted-foreground">{isClient ? "No upcoming absences in the next 7 days." : "Loading chart..."}</p>
              </div>
            )}
          </CardContent>
        </Card>
        
        <Card className="shadow-lg md:col-span-2">
            <CardHeader>
            <CardTitle className="flex items-center gap-2">
                <LucideBarChart className="h-5 w-5 text-primary" />
                Team Overview (Placeholder)
            </CardTitle>
            </CardHeader>
            <CardContent className="h-64 flex items-center justify-center">
            <Image src="https://picsum.photos/800/300?random=1" alt="Placeholder chart" width={800} height={300} className="rounded-md object-cover" data-ai-hint="chart graph" />
            </CardContent>
        </Card>
      </div>
    </div>
  );
}
