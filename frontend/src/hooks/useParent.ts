import { useQuery } from '@tanstack/react-query';
import { api } from '@/services/api';
import { Player, Attendance, Event } from '@/types';

// Get parent's children
export function useMyChildren() {
  return useQuery<Player[]>({
    queryKey: ['my-children'],
    queryFn: async () => {
      const response = await api.get<Player[]>('/parents/children');
      return response;
    },
  });
}

// Get child's attendance (parent view)
export function useChildAttendance(childId: string) {
  return useQuery<Attendance[]>({
    queryKey: ['child-attendance', childId],
    queryFn: async () => {
      const response = await api.get<Attendance[]>(`/attendance/player/${childId}`);
      return response;
    },
    enabled: !!childId,
  });
}

// Get child's team events (parent view)
export function useChildTeamEvents(teamId: string | undefined) {
  return useQuery<Event[]>({
    queryKey: ['child-team-events', teamId],
    queryFn: async () => {
      const response = await api.get<Event[]>('/events', { team_id: teamId });
      return response;
    },
    enabled: !!teamId,
  });
}
