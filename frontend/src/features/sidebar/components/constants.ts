import { Home, Logs } from 'lucide-react';
import type { SidebarItem } from '@/features/sidebar/types';

export const items: SidebarItem[] = [
  {
    title: 'Home',
    url: '/home',
    icon: Home,
  },
  {
    title: 'Standings',
    url: '/standings',
    icon: Logs,
  },
];
