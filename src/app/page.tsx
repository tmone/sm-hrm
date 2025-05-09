import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { APP_NAME } from '@/lib/constants';
import { Building, LogIn } from 'lucide-react';

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-br from-primary/10 via-background to-background p-6">
      <div className="max-w-2xl text-center space-y-8 bg-card p-8 sm:p-12 rounded-xl shadow-2xl">
        <div className="flex justify-center items-center space-x-3">
          <Building className="h-12 w-12 text-primary" />
          <h1 className="text-5xl font-bold tracking-tight text-primary">
            {APP_NAME}
          </h1>
        </div>
        
        <p className="text-lg text-muted-foreground">
          Your comprehensive solution for Human Resource Management. Streamline operations, manage employees, and gain valuable insights.
        </p>
        
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Button asChild size="lg" className="shadow-md hover:shadow-lg transition-shadow">
            <Link href="/dashboard">
              <LogIn className="mr-2 h-5 w-5" /> Go to Dashboard
            </Link>
          </Button>
          <Button variant="outline" size="lg" className="shadow-md hover:shadow-lg transition-shadow">
            Learn More
          </Button>
        </div>
        
        <p className="text-sm text-muted-foreground/80 pt-4">
          &copy; {new Date().getFullYear()} {APP_NAME}. All rights reserved.
        </p>
      </div>
    </div>
  );
}
