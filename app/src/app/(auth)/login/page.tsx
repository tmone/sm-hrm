'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { APP_NAME } from '@/lib/constants';
import { Building, LogIn } from 'lucide-react';
import { useState, type FormEvent, useEffect } from 'react';
import { useToast } from '@/hooks/use-toast';
import { useAuth } from '@/contexts/auth-context';

export default function LoginPage() {
  const router = useRouter();
  const { toast } = useToast();
  const { login, isAuthenticated, isLoading: authLoading } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, router]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsLoading(true);

    try {
      // Call the login function from auth context
      await login(username, password);
      // The auth context will handle redirecting to dashboard
      toast({
        title: 'Login Successful',
        description: 'Redirecting to dashboard...',
      });
    } catch (error) {
      console.error('Login error:', error);
      toast({
        variant: 'destructive',
        title: 'Login Failed',
        description: 'Invalid username or password. Please try again.',
      });
      setIsLoading(false);
    }
  };

  return (
    <Card className="w-full max-w-md shadow-2xl rounded-xl">
      <CardHeader className="space-y-2 text-center pt-8">
        <div className="flex justify-center items-center space-x-3 mb-4">
            <Building className="h-10 w-10 text-primary" />
            <CardTitle className="text-4xl font-bold tracking-tight text-primary">{APP_NAME}</CardTitle>
        </div>
        <CardDescription className="text-md">Enter your credentials to access your account</CardDescription>
      </CardHeader>
      <CardContent className="p-6 sm:p-8">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="username">Username</Label>
            <Input
              id="username"
              type="text"
              placeholder="admin"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={isLoading || authLoading}
              className="text-base"
            />
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="password">Password</Label>
              <Link href="#" className="text-sm text-primary hover:underline" onClick={(e) => {e.preventDefault(); toast({title: "Feature not implemented", description: "Password recovery is not yet available."})}}>
                Forgot password?
              </Link>
            </div>
            <Input
              id="password"
              type="password"
              placeholder="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={isLoading || authLoading}
              className="text-base"
            />
          </div>
          <Button type="submit" className="w-full shadow-md hover:shadow-lg transition-shadow py-3 text-base" disabled={isLoading || authLoading} size="lg">
            {isLoading || authLoading ? (
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary-foreground"></div>
            ) : (
              <><LogIn className="mr-2 h-5 w-5" /> Login</>
            )}
          </Button>
        </form>
        <div className="mt-6 text-center text-sm">
          Don&apos;t have an account?{' '}
          <Link href="#" className="text-primary hover:underline" onClick={(e) => {e.preventDefault(); toast({title: "Feature not implemented", description: "Account registration is not yet available."})}}>
            Sign up
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
