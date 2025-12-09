import { AlignHorizontalSpaceAround, Grid3X3, Home, Logs } from 'lucide-react';
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
    icon: AlignHorizontalSpaceAround,
  },
  {
    title: 'Standings',
    url: '/standings',
    icon: Logs,
  },
  {
    title: 'Draft',
    url: '/draft',
    icon: Grid3X3,
  },
];
