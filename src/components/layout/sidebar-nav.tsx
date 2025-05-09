"use client";

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { NAV_ITEMS, SETTINGS_NAV_ITEMS, APP_NAME, type NavItem } from '@/lib/constants';
import {
  Sidebar,
  SidebarHeader,
  SidebarContent,
  SidebarFooter,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarSeparator,
} from "@/components/ui/sidebar";
import { Building, LogOut } from 'lucide-react';

interface SidebarNavProps {
  className?: string;
}

function NavLink({ item }: { item: NavItem }) {
  const pathname = usePathname();
  const isActive = item.match ? item.match(pathname) : pathname.startsWith(item.href);

  return (
    <SidebarMenuItem>
      <Link href={item.href} legacyBehavior passHref>
        <SidebarMenuButton
          isActive={isActive}
          tooltip={{ children: item.label, className: "bg-card text-card-foreground border-border shadow-md" }}
        >
          <item.icon />
          <span>{item.label}</span>
        </SidebarMenuButton>
      </Link>
    </SidebarMenuItem>
  );
}

export function SidebarNav({ className }: SidebarNavProps) {
  return (
    <Sidebar collapsible="icon" side="left" variant="sidebar" className={cn(className)}>
      <SidebarHeader className="border-b">
        <Link href="/dashboard" className="flex items-center gap-2 group-data-[collapsible=icon]:justify-center">
          <Building className="h-7 w-7 text-primary transition-all group-hover:scale-110" />
          <span className="text-lg font-semibold text-primary group-data-[collapsible=icon]:hidden">
            {APP_NAME}
          </span>
        </Link>
      </SidebarHeader>
      <SidebarContent className="p-2">
        <SidebarMenu>
          {NAV_ITEMS.map((item) => (
            <NavLink key={item.href} item={item} />
          ))}
        </SidebarMenu>
      </SidebarContent>
      <SidebarSeparator />
      <SidebarFooter className="p-2">
        <SidebarMenu>
          {SETTINGS_NAV_ITEMS.map((item) => (
             <NavLink key={item.href} item={item} />
          ))}
          <SidebarMenuItem>
             <SidebarMenuButton tooltip={{ children: "Logout", className: "bg-card text-card-foreground border-border shadow-md"}}>
                <LogOut />
                <span>Logout</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  );
}
