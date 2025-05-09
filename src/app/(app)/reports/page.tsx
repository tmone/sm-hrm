import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart, CalendarDays, PieChart, Users } from "lucide-react";
import Image from "next/image";
import { ChartContainer, ChartTooltip, ChartTooltipContent, ChartLegend, ChartLegendContent } from "@/components/ui/chart";
import { Bar, CartesianGrid, XAxis, YAxis, Pie, Cell, ResponsiveContainer, Tooltip as RechartsTooltip, Legend as RechartsLegend } from "recharts";
import type { ChartConfig } from "@/components/ui/chart";

const attendanceData = [
  { month: "Jan", present: 186, absent: 30, late: 12 },
  { month: "Feb", present: 190, absent: 20, late: 15 },
  { month: "Mar", present: 205, absent: 15, late: 8 },
  { month: "Apr", present: 195, absent: 25, late: 10 },
  { month: "May", present: 210, absent: 10, late: 5 },
  { month: "Jun", present: 200, absent: 18, late: 7 },
];

const chartConfig = {
  present: { label: "Present", color: "hsl(var(--chart-2))" },
  absent: { label: "Absent", color: "hsl(var(--chart-3))" },
  late: { label: "Late", color: "hsl(var(--chart-4))" },
} satisfies ChartConfig;

const departmentDistributionData = [
  { name: 'Engineering', value: 400, fill: 'hsl(var(--chart-1))' },
  { name: 'Marketing', value: 300, fill: 'hsl(var(--chart-2))' },
  { name: 'Sales', value: 300, fill: 'hsl(var(--chart-3))' },
  { name: 'HR', value: 200, fill: 'hsl(var(--chart-4))' },
  { name: 'Support', value: 278, fill: 'hsl(var(--chart-5))' },
];


export default function ReportsPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold tracking-tight text-foreground">Reports & Analytics</h1>
      <p className="text-muted-foreground">Visualize attendance and leave data.</p>

      <div className="grid gap-6 md:grid-cols-1 lg:grid-cols-2">
        <Card className="shadow-xl">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
                <BarChart className="h-5 w-5 text-primary" />
                Monthly Attendance Trends
            </CardTitle>
            <CardDescription>Overview of employee attendance over the past 6 months.</CardDescription>
          </CardHeader>
          <CardContent>
            <ChartContainer config={chartConfig} className="h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={attendanceData} margin={{ top: 5, right: 20, left: -20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="month" tickLine={false} axisLine={false} tickMargin={8} />
                  <YAxis tickLine={false} axisLine={false} tickMargin={8} />
                  <ChartTooltip content={<ChartTooltipContent />} />
                  <ChartLegend content={<ChartLegendContent />} />
                  <Bar dataKey="present" fill="var(--color-present)" radius={4} />
                  <Bar dataKey="absent" fill="var(--color-absent)" radius={4} />
                  <Bar dataKey="late" fill="var(--color-late)" radius={4} />
                </BarChart>
              </ResponsiveContainer>
            </ChartContainer>
          </CardContent>
        </Card>

        <Card className="shadow-xl">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
                <PieChart className="h-5 w-5 text-primary" />
                Employee Distribution by Department
            </CardTitle>
            <CardDescription>Breakdown of employees across different departments.</CardDescription>
          </CardHeader>
          <CardContent className="flex items-center justify-center">
             <ChartContainer config={{}} className="h-[300px] w-full">
               <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={departmentDistributionData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} label>
                    {departmentDistributionData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Pie>
                  <RechartsTooltip />
                  <RechartsLegend />
                </PieChart>
              </ResponsiveContainer>
            </ChartContainer>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
                <CalendarDays className="h-5 w-5 text-primary" />
                Leave Type Distribution (Placeholder)
            </CardTitle>
          </CardHeader>
          <CardContent className="h-64 flex items-center justify-center">
            <Image src="https://picsum.photos/400/300?random=2" alt="Placeholder chart" width={400} height={300} className="rounded-md object-cover" data-ai-hint="pie chart" />
          </CardContent>
        </Card>
         <Card className="shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5 text-primary" />
                Headcount Growth Over Time (Placeholder)
            </CardTitle>
          </CardHeader>
          <CardContent className="h-64 flex items-center justify-center">
            <Image src="https://picsum.photos/400/300?random=3" alt="Placeholder chart" width={400} height={300} className="rounded-md object-cover" data-ai-hint="line graph" />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
