import type { LucideIcon } from 'lucide-react';
import { LayoutDashboard, Users, CalendarClock, Plane, LineChart, Settings, ScanFace } from 'lucide-react';

export const APP_NAME = "StepMedia HRM";

export interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
  match?: (pathname: string) => boolean;
}

export const NAV_ITEMS: NavItem[] = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/employees", label: "Employees", icon: Users },
  { href: "/attendance", label: "Attendance", icon: CalendarClock },
  { href: "/leave", label: "Leave", icon: Plane },
  { href: "/facial-recognition", label: "Face Registration", icon: ScanFace },
  { href: "/reports", label: "Reports", icon: LineChart },
];

export const SETTINGS_NAV_ITEMS: NavItem[] = [
 { href: "/settings", label: "Settings", icon: Settings },
];
