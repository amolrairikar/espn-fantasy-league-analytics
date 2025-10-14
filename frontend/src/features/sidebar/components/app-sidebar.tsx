import { Home, Logs, PanelLeftClose, PanelLeftOpen } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from '@/components/ui/sidebar';
import type { SidebarItem } from '@/features/sidebar/types';

const items: SidebarItem[] = [
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

function AppSidebar() {
  const { open, toggleSidebar } = useSidebar();
  return (
    <Sidebar collapsible="icon">
      {/* Top section with collapse toggle */}
      <div className="flex items-center justify-between p-2 border-b border-border">
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleSidebar}
          className="hover:bg-accent transition-colors cursor-pointer"
        >
          {open ? <PanelLeftClose className="h-5 w-5" /> : <PanelLeftOpen className="h-5 w-5" />}
        </Button>
      </div>

      {/* Main sidebar content */}
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {items.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild>
                    <Link to={item.url} className="flex items-center gap-2">
                      <item.icon className="h-4 w-4" />
                      <span>{item.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}

export default AppSidebar;
