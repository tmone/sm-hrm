import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { CheckCircle, Clock, XCircle, Users } from 'lucide-react';

interface StatsProps {
  stats: {
    total: number;
    approved: number;
    pending: number;
    rejected: number;
  };
}

export default function RegistrationStats({ stats }: StatsProps) {
  return (
    <div className="grid gap-4 md:grid-cols-4">
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center gap-4">
            <div className="rounded-full bg-blue-50 p-3">
              <Users className="h-5 w-5 text-blue-700" />
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Total Registered</p>
              <h3 className="text-2xl font-bold">{stats.total}</h3>
            </div>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center gap-4">
            <div className="rounded-full bg-green-50 p-3">
              <CheckCircle className="h-5 w-5 text-green-700" />
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Approved</p>
              <h3 className="text-2xl font-bold">{stats.approved}</h3>
            </div>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center gap-4">
            <div className="rounded-full bg-yellow-50 p-3">
              <Clock className="h-5 w-5 text-yellow-700" />
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Pending</p>
              <h3 className="text-2xl font-bold">{stats.pending}</h3>
            </div>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center gap-4">
            <div className="rounded-full bg-red-50 p-3">
              <XCircle className="h-5 w-5 text-red-700" />
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Rejected</p>
              <h3 className="text-2xl font-bold">{stats.rejected}</h3>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}