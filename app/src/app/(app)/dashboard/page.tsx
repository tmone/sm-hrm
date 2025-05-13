'use client';

import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { DataCard } from "@/components/shared/data-card";
import { BarChart as LucideBarChart, CalendarDays, CheckCircle, Users, CalendarX, Briefcase, UserCheck, ScanFace, Loader2 } from "lucide-react";
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
import { format } from 'date-fns';
import type { ChartConfig } from "@/components/ui/chart";
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import dynamic from 'next/dynamic';
import { fetchDashboardSummary, fetchTodayAttendance, fetchUpcomingLeaves, fetchUpcomingAbsencesData } from '@/lib/dashboard-api';
import { useToast } from '@/hooks/use-toast';

// Dynamically import Recharts components
const ResponsiveContainer = dynamic(() => import('recharts').then(mod => mod.ResponsiveContainer), { ssr: false, loading: () => <p className="text-center text-muted-foreground py-8">Loading chart...</p> });
const RechartsBarChartPrimitive = dynamic(() => import('recharts').then(mod => mod.BarChart), { ssr: false, loading: () => <p className="text-center text-muted-foreground py-8">Loading chart...</p> });
const CartesianGrid = dynamic(() => import('recharts').then(mod => mod.CartesianGrid), { ssr: false });
const XAxis = dynamic(() => import('recharts').then(mod => mod.XAxis), { ssr: false });
const YAxis = dynamic(() => import('recharts').then(mod => mod.YAxis), { ssr: false });
const Bar = dynamic(() => import('recharts').then(mod => mod.Bar), { ssr: false });

const upcomingAbsencesChartConfig = {
  absentCount: { label: "Absent Employees", color: "hsl(var(--chart-4))" },
} satisfies ChartConfig;

export default function DashboardPage() {
  const { toast } = useToast();
  const [isLoading, setIsLoading] = React.useState(true);
  const [isClient, setIsClient] = React.useState(false);
  const [summaryMetrics, setSummaryMetrics] = React.useState<any[]>([]);
  const [todayAttendance, setTodayAttendance] = React.useState<any[]>([]);
  const [upcomingLeaves, setUpcomingLeaves] = React.useState<any[]>([]);
  const [upcomingAbsencesData, setUpcomingAbsencesData] = React.useState<any[]>([]);

  // Set isClient to true once component is mounted
  React.useEffect(() => {
    setIsClient(true);
  }, []);

  // Fetch all dashboard data
  React.useEffect(() => {
    const loadDashboardData = async () => {
      try {
        setIsLoading(true);
        
        // Fetch dashboard summary
        const summary = await fetchDashboardSummary();
        
        // Create metrics array from the summary data
        const metrics = [
          { 
            label: 'Total Employees', 
            value: summary.totalEmployees, 
            icon: Users, 
            change: summary.newEmployeesThisMonth ? `+${summary.newEmployeesThisMonth} this month` : '', 
            changeType: 'positive' as const 
          },
          { 
            label: 'On Leave Today', 
            value: summary.onLeaveToday, 
            icon: CalendarX, 
            change: '', 
            changeType: 'neutral' as const 
          },
          { 
            label: 'Present Today', 
            value: summary.presentToday, 
            icon: UserCheck, 
            change: '', 
            changeType: 'neutral' as const 
          },
          { 
            label: 'Pending Leave Requests', 
            value: summary.pendingLeaveRequests, 
            icon: Briefcase, 
            change: '', 
            changeType: 'neutral' as const 
          },
          { 
            label: 'Registered Faces', 
            value: `${summary.registeredFaces.approved} / ${summary.registeredFaces.total}`, 
            icon: ScanFace, 
            description: 'Approved / Total', 
            changeType: 'positive' as const 
          },
        ];
        setSummaryMetrics(metrics);
        
        // Fetch today's attendance
        const attendanceData = await fetchTodayAttendance();
        setTodayAttendance(attendanceData.slice(0, 5)); // Show top 5
        
        // Fetch upcoming leaves
        const leavesData = await fetchUpcomingLeaves();
        setUpcomingLeaves(leavesData.slice(0, 3)); // Show top 3
        
        // Fetch upcoming absences data for the chart
        const absencesData = await fetchUpcomingAbsencesData();
        setUpcomingAbsencesData(absencesData);
        
      } catch (error) {
        console.error('Error loading dashboard data:', error);
        toast({
          title: 'Failed to load dashboard data',
          description: 'There was an error fetching the dashboard information',
          variant: 'destructive'
        });
      } finally {
        setIsLoading(false);
      }
    };
    
    if (isClient) {
      loadDashboardData();
    }
  }, [isClient, toast]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-80">
        <div className="text-center space-y-4">
          <Loader2 className="h-10 w-10 animate-spin text-primary mx-auto" />
          <p className="text-muted-foreground">Loading dashboard data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold tracking-tight text-foreground">Dashboard</h1>
      
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {summaryMetrics.map((metric, index) => (
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
            {todayAttendance.length > 0 ? (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Employee</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {todayAttendance.map((att) => (
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
      </div>
    </div>
  );
}