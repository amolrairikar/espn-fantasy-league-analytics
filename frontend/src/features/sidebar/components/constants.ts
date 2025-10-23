import { Grid2X2, Home, Logs } from 'lucide-react';
import type { SidebarItem } from '@/features/sidebar/types';

export const items: SidebarItem[] = [
  {
    title: 'Home',
    url: '/home',
    icon: Home,
  },
  {
    title: 'Scores',
    url: '/scores',
    icon: Grid2X2,
  },
  {
    title: 'Standings',
    url: '/standings',
    icon: Logs,
  },
];
