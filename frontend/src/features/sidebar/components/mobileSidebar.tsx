import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { items } from '@/features/sidebar/components/constants';
import type { SidebarItem } from '@/features/sidebar/types';

interface MobileSidebarProps {
  onNavigate?: () => void;
}

function MobileSidebar({ onNavigate }: MobileSidebarProps) {
  return (
    <nav className="flex flex-col gap-2 p-4">
      {items.map((item: SidebarItem) => (
        <Button asChild variant="ghost" className="justify-start gap-2" key={item.title} onClick={onNavigate}>
          <Link to={item.url}>
            <item.icon className="h-5 w-5" />
            {item.title}
          </Link>
        </Button>
      ))}
    </nav>
  );
}

export default MobileSidebar;
