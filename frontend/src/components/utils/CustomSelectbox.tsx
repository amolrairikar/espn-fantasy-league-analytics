import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface ReusableSelectProps {
  title: string;
  placeholder: string;
  items: string[];
  onValueChange?: (value: string) => void;
  defaultValue?: string;
  value?: string | null;
  className?: string;
}

export function CustomSelect({ 
  title,
  placeholder,
  items,
  onValueChange,
  defaultValue,
  value,
}: ReusableSelectProps) {
  return (
    <div className="flex flex-col items-center">
      <label className="text-sm font-medium text-muted-foreground text-center mb-1.5">
        {title}
      </label>
      <Select onValueChange={onValueChange} defaultValue={defaultValue} value={value ?? undefined}>
        <SelectTrigger className="w-45">
          <SelectValue placeholder={placeholder} />
        </SelectTrigger>
        <SelectContent>
          <SelectGroup>
            {items.map((item) => (
              <SelectItem key={item} value={item}>
                {item}
              </SelectItem>
            ))}
          </SelectGroup>
        </SelectContent>
      </Select>
    </div>
  );
}