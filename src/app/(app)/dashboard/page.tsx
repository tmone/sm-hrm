import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { DataCard } from "@/components/shared/data-card";
import { dashboardSummaryMetrics, mockAttendance, mockLeaveRequests } from "@/lib/data";
import { BarChart, CalendarDays, CheckCircle, Users } from "lucide-react";
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

export default function DashboardPage() {
  const today = new Date().toISOString().split('T')[0];
  const recentAttendance = mockAttendance.filter(a => a.date === today).slice(0, 5);
  const upcomingLeaves = mockLeaveRequests.filter(lr => lr.status === 'Approved' && new Date(lr.startDate) >= new Date()).slice(0,3);

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold tracking-tight text-foreground">Dashboard</h1>
      
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {dashboardSummaryMetrics.map((metric) => (
          <DataCard 
            key={metric.label}
            title={metric.label}
            value={metric.value.toString()}
            icon={metric.icon}
            description={metric.change}
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
      </div>
      
      <Card className="shadow-lg">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart className="h-5 w-5 text-primary" />
            Team Overview (Placeholder)
          </CardTitle>
        </CardHeader>
        <CardContent className="h-64 flex items-center justify-center">
          <Image src="https://picsum.photos/800/300?random=1" alt="Placeholder chart" width={800} height={300} className="rounded-md object-cover" data-ai-hint="chart graph" />
        </CardContent>
      </Card>
    </div>
  );
}
