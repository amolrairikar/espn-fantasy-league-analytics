import { useState, useEffect } from 'react';
import { useGetResource } from '@/components/hooks/genericGetRequest';

export function useGetAllTimeRecord<T>(leagueId: string, platform: string, recordType: string) {
  const [data, setData] = useState<T>();
  const { refetch } = useGetResource<T>(`/alltime_records`, {
    league_id: leagueId,
    platform,
    record_type: recordType,
  });

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await refetch();
        if (response?.data?.data) setData(response.data.data);
      } catch (err) {
        console.error(err);
      }
    };

    void fetchData();
  }, [refetch]);

  return data;
}
