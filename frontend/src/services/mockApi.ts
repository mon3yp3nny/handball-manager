import { User, UserRole, Team, Player, Game, Event, News, Attendance } from '@/types';

// Mock data for development without backend
const mockUsers: User[] = [
  {
    id: '1',
    email: 'admin@handball.de',
    first_name: 'Max',
    last_name: 'Admin',
    role: UserRole.ADMIN,
    phone: '+49 123 456789',
    created_at: '2024-01-15T10:00:00Z',
    is_active: true,
  },
  {
    id: '2',
    email: 'coach@handball.de',
    first_name: 'Thomas',
    last_name: 'Trainer',
    role: UserRole.COACH,
    phone: '+49 123 456790',
    created_at: '2024-01-15T10:00:00Z',
    is_active: true,
  },
  {
    id: '3',
    email: 'spieler@handball.de',
    first_name: 'Lukas',
    last_name: 'Müller',
    role: UserRole.PLAYER,
    phone: '+49 123 456792',
    created_at: '2024-01-15T10:00:00Z',
    is_active: true,
  },
  {
    id: '4',
    email: 'eltern@handball.de',
    first_name: 'Maria',
    last_name: 'Schmidt',
    role: UserRole.PARENT,
    phone: '+49 123 456793',
    created_at: '2024-01-15T10:00:00Z',
    is_active: true,
  },
];

const mockTeams: Team[] = [
  {
    id: '1',
    name: '1. Herren',
    description: 'Männermannschaft erste Liga',
    age_group: 'Erwachsene',
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:00:00Z',
    player_count: 18,
    coach_name: 'Thomas Trainer',
  },
  {
    id: '2',
    name: 'U14 männlich',
    description: 'Jugendmannschaft U14',
    age_group: 'U14',
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:00:00Z',
    player_count: 14,
    coach_name: 'Max Admin',
  },
  {
    id: '3',
    name: 'U16 weiblich',
    description: 'Mädchenmannschaft U16',
    age_group: 'U16',
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:00:00Z',
    player_count: 12,
    coach_name: 'Anna Betreuer',
  },
];

const mockPlayers: Player[] = [
  {
    id: '1',
    user: mockUsers[2],
    user_id: '3',
    team_id: '1',
    jersey_number: 7,
    position: 'RL',
    joined_date: '2024-01-15',
    games_played: 15,
    goals_scored: 42,
    birth_date: '2005-03-10',
    emergency_contact: 'Vater: +49 123 456793',
  },
  {
    id: '2',
    user: { id: '5', email: 'julian@test.de', first_name: 'Julian', last_name: 'Weber', role: UserRole.PLAYER, is_active: true, created_at: '2024-01-15T10:00:00Z' },
    user_id: '5',
    team_id: '1',
    jersey_number: 10,
    position: 'KM',
    games_played: 15,
    goals_scored: 28,
  },
  {
    id: '3',
    user: { id: '6', email: 'felix@test.de', first_name: 'Felix', last_name: 'Koch', role: UserRole.PLAYER, is_active: true, created_at: '2024-01-15T10:00:00Z' },
    user_id: '6',
    team_id: '1',
    jersey_number: 1,
    position: 'TW',
    games_played: 15,
    goals_scored: 0,
  },
  {
    id: '4',
    user: { id: '7', email: 'lisa@test.de', first_name: 'Lisa', last_name: 'Meyer', role: UserRole.PLAYER, is_active: true, created_at: '2024-01-15T10:00:00Z' },
    user_id: '7',
    team_id: '3',
    jersey_number: 8,
    position: 'LA',
    games_played: 12,
    goals_scored: 35,
  },
  {
    id: '5',
    user: { id: '8', email: 'lena@test.de', first_name: 'Lena', last_name: 'Fischer', role: UserRole.PLAYER, is_active: true, created_at: '2024-01-15T10:00:00Z' },
    user_id: '8',
    team_id: '3',
    jersey_number: 9,
    position: 'RA',
    games_played: 12,
    goals_scored: 31,
  },
];

const mockGames: Game[] = [
  {
    id: '1',
    team_id: '1',
    team_name: '1. Herren',
    opponent: 'TSV Hamburg',
    opponent_logo: null,
    scheduled_at: '2024-02-20T19:00:00Z',
    location: 'Sporthalle Mitte, Hamburg',
    home_score: 28,
    away_score: 24,
    status: 'completed',
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-02-20T21:00:00Z',
  },
  {
    id: '2',
    team_id: '1',
    team_name: '1. Herren',
    opponent: 'VfL Berlin',
    opponent_logo: null,
    scheduled_at: '2024-02-27T19:00:00Z',
    location: 'Sporthalle Ost, Berlin',
    home_score: null,
    away_score: null,
    status: 'scheduled',
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:00:00Z',
  },
  {
    id: '3',
    team_id: '3',
    team_name: 'U16 weiblich',
    opponent: 'SG Leipzig',
    opponent_logo: null,
    scheduled_at: '2024-02-18T16:00:00Z',
    location: 'Jugendsporthalle Leipzig',
    home_score: null,
    away_score: null,
    status: 'scheduled',
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:00:00Z',
  },
  {
    id: '4',
    team_id: '3',
    team_name: 'U16 weiblich',
    opponent: 'Dresdner SC',
    opponent_logo: null,
    scheduled_at: '2024-02-25T14:00:00Z',
    location: 'Sporthalle Mitte, Hamburg',
    home_score: null,
    away_score: null,
    status: 'scheduled',
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:00:00Z',
  },
];

const mockEvents: Event[] = [
  {
    id: '1',
    title: 'Mannschaftstraining',
    description: 'Reguläres Training',
    start_time: '2024-02-18T18:00:00Z',
    end_time: '2024-02-18T20:00:00Z',
    location: 'Sporthalle Mitte',
    event_type: 'training',
    team_id: '1',
    created_by: '2',
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:00:00Z',
  },
  {
    id: '2',
    title: 'Vereinsversammlung',
    description: 'Jährliche Mitgliederversammlung',
    start_time: '2024-02-22T19:00:00Z',
    end_time: '2024-02-22T21:00:00Z',
    location: 'Vereinsheim',
    event_type: 'meeting',
    team_id: null,
    created_by: '1',
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:00:00Z',
  },
  {
    id: '3',
    title: 'Jugendturnier',
    description: 'Internationales Jugendhandballturnier',
    start_time: '2024-03-02T09:00:00Z',
    end_time: '2024-03-03T18:00:00Z',
    location: 'Sportpark Hamburg',
    event_type: 'tournament',
    team_id: '3',
    created_by: '2',
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:00:00Z',
  },
];

const mockNews: News[] = [
  {
    id: '1',
    title: 'Sieg gegen TSV Hamburg',
    content: 'Unsere erste Herren gewinnt das Heimspiel gegen den TSV Hamburg mit 28:24. Besonders hervorzuheben ist die starke zweite Halbzeit.',
    team_id: '1',
    created_by: '2',
    created_at: '2024-02-20T22:00:00Z',
    updated_at: '2024-02-20T22:00:00Z',
    author_name: 'Thomas Trainer',
  },
  {
    id: '2',
    title: 'Neue Trainingszeiten',
    content: 'Ab nächster Woche trainieren wir Dienstags und Donnerstags jeweils von 18:00 bis 20:00 Uhr.',
    team_id: null,
    created_by: '1',
    created_at: '2024-02-15T10:00:00Z',
    updated_at: '2024-02-15T10:00:00Z',
    author_name: 'Max Admin',
  },
];

// Mock API methods
const mockApi = {
  get: async (endpoint: string): Promise<any> => {
    await delay(200); // Simulate network delay
    
    if (endpoint.includes('/teams')) {
      return { items: mockTeams, total: mockTeams.length };
    }
    if (endpoint.includes('/players')) {
      return { items: mockPlayers, total: mockPlayers.length };
    }
    if (endpoint.includes('/games')) {
      return { items: mockGames, total: mockGames.length };
    }
    if (endpoint.includes('/events')) {
      return { items: mockEvents, total: mockEvents.length };
    }
    if (endpoint.includes('/news')) {
      return { items: mockNews, total: mockNews.length };
    }
    
    return {};
  },
  
  post: async (endpoint: string, data: any): Promise<any> => {
    await delay(200);
    return { success: true, ...data, id: Math.random().toString() };
  },
  
  patch: async (endpoint: string, data: any): Promise<any> => {
    await delay(200);
    return { success: true, ...data };
  },
  
  delete: async (endpoint: string): Promise<any> => {
    await delay(200);
    return { success: true };
  },
  
  // Auth
  login: async (email: string, password: string): Promise<{ user: User; access_token: string } | null> => {
    await delay(500);
    const user = mockUsers.find(u => u.email === email);
    if (!user) {
      throw new Error('Ungültige Anmeldedaten');
    }
    return { user, access_token: 'mock-token-' + user.id };
  },
  
  getMe: async (): Promise<User | null> => {
    await delay(200);
    // Return first user as default logged in user
    return mockUsers[0];
  },
};

function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export default mockApi;
export { mockUsers, mockTeams, mockPlayers, mockGames, mockEvents, mockNews };
