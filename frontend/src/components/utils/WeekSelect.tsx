import { useEffect, useState } from 'react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

interface WeekSelectProps {
  season?: string;
  defaultWeek?: string | number;
  onWeekChange: (week: string) => void;
  className?: string;
}

export function WeekSelect({ season, defaultWeek, onWeekChange, className }: WeekSelectProps) {
  const [weeks, setWeeks] = useState<string[]>([]);
  const [selectedWeek, setSelectedWeek] = useState<string | undefined>(defaultWeek?.toString());

  useEffect(() => {
    if (!season) {
      setWeeks([]);
      return;
    }

    // Determine week count: 17 weeks before 2021, 18 weeks from 2021 onward
    const numericSeason = Number(season);
    const totalWeeks = numericSeason >= 2021 ? 18 : 17;

    const weekArray = Array.from({ length: totalWeeks }, (_, i) => (i + 1).toString());
    setWeeks(weekArray);

    // Default to week 1 if nothing selected
    if (!selectedWeek) {
      const initial = defaultWeek?.toString() ?? '1';
      setSelectedWeek(initial);
      onWeekChange(initial);
    }
  }, [season, defaultWeek, onWeekChange, selectedWeek]);

  const handleWeekChange = (value: string) => {
    setSelectedWeek(value);
    onWeekChange(value);
  };

  return (
    <div className={`flex items-center space-x-4 ${className ?? ''}`}>
      <label htmlFor="week" className="font-medium text-sm w-20 md:w-auto">
        Week:
      </label>
      <Select onValueChange={handleWeekChange} value={selectedWeek} disabled={!weeks.length}>
        <SelectTrigger className="w-50">
          <SelectValue placeholder="Select a week" />
        </SelectTrigger>
        <SelectContent>
          {weeks.length > 0 ? (
            weeks.map((week) => (
              <SelectItem key={week} value={week}>
                {week}
              </SelectItem>
            ))
          ) : (
            <SelectItem disabled value="none">
              Select a season first
            </SelectItem>
          )}
        </SelectContent>
      </Select>
    </div>
  );
}
