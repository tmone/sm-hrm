// @ts-nocheck
// TODO: Fix typings
'use client';

import Link from 'next/link';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Building, LogOut, Settings, UserCircle } from "lucide-react";
import { APP_NAME } from '@/lib/constants';
import { ThemeToggle } from '@/components/theme-toggle';
import { SidebarTrigger, useSidebar } from '@/components/ui/sidebar';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/auth-context';

export function AppHeader() {
  const { isMobile } = useSidebar();
  const [mounted, setMounted] = useState(false);
  const router = useRouter();
  const { user, logout } = useAuth();

  useEffect(() => {
    setMounted(true);
  }, []);

  const handleLogout = () => {
    logout();
    // The auth context will handle redirecting to login
  };
  
  const handleNavigate = (path: string) => {
    router.push(path);
  }

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center gap-4 border-b bg-background/80 px-4 backdrop-blur-md sm:static sm:h-auto sm:border-0 sm:bg-transparent sm:px-6">
      {mounted && isMobile && <SidebarTrigger />}
      
      <div className="flex items-center gap-2">
        <Building className="h-6 w-6 text-primary" />
        <h1 className="text-xl font-semibold text-primary">{APP_NAME}</h1>
      </div>
      
      <div className="ml-auto flex items-center gap-2">
        <ThemeToggle />
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="outline"
              size="icon"
              className="overflow-hidden rounded-full h-9 w-9"
            >
              <Avatar className="h-9 w-9">
                <AvatarImage src="https://picsum.photos/40/40" alt="User Avatar" data-ai-hint="person face" />
                <AvatarFallback>
                  <UserCircle />
                </AvatarFallback>
              </Avatar>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel>{user?.full_name || 'My Account'}</DropdownMenuLabel>
            <DropdownMenuItem disabled className="text-xs opacity-50">
              <span>{user?.email || ''}</span>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onSelect={() => handleNavigate('/settings')}>
              <Settings className="mr-2 h-4 w-4" />
              <span>Settings</span>
            </DropdownMenuItem>
            <DropdownMenuItem onSelect={() => handleNavigate('/settings')}>
              {/* Assuming profile is part of settings for now */}
              <UserCircle className="mr-2 h-4 w-4" />
              <span>Profile</span>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onSelect={handleLogout}>
              <LogOut className="mr-2 h-4 w-4" />
              <span>Logout</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
