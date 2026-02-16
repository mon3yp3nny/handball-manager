// User Types
export enum UserRole {
  ADMIN = 'admin',
  COACH = 'coach',
  SUPERVISOR = 'supervisor',
  PLAYER = 'player',
  PARENT = 'parent',
}

export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  phone?: string;
  role: UserRole;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserLogin {
  email: string;
  password: string;
}

export interface UserRegister {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  phone?: string;
  role: UserRole;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// Team Types
export interface Team {
  id: number;
  name: string;
  description?: string;
  age_group?: string;
  coach_id?: number;
  created_at: string;
  updated_at: string;
  player_count?: number;
}

export interface TeamWithPlayers extends Team {
  players: Player[];
}

// Player Types
export enum Position {
  GOALKEEPER = 'goalkeeper',
  LEFT_WING = 'left_wing',
  LEFT_BACK = 'left_back',
  CENTER_BACK = 'center_back',
  RIGHT_BACK = 'right_back',
  RIGHT_WING = 'right_wing',
  PIVOT = 'pivot',
  DEFENSE = 'defense',
}

export interface Player {
  id: number;
  user_id: number;
  team_id?: number;
  jersey_number?: number;
  position?: Position;
  date_of_birth?: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  games_played: number;
  goals_scored: number;
  assists: number;
  created_at: string;
  updated_at: string;
  user?: User;
}

// Game Types
export enum GameStatus {
  SCHEDULED = 'scheduled',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled',
}

export enum GameType {
  LEAGUE = 'league',
  TOURNAMENT = 'tournament',
  FRIENDLY = 'friendly',
  CUP = 'cup',
}

export interface Game {
  id: number;
  team_id: number;
  opponent: string;
  location: string;
  scheduled_at: string;
  game_type: GameType;
  status: GameStatus;
  home_score?: number;
  away_score?: number;
  is_home_game: boolean;
  notes?: string;
  created_at: string;
  updated_at: string;
  team_name?: string;
}

// Event Types
export enum EventType {
  TRAINING = 'training',
  MEETING = 'meeting',
  TOURNAMENT = 'tournament',
  OTHER = 'other',
}

export interface Event {
  id: number;
  title: string;
  description?: string;
  team_id: number;
  event_type: EventType;
  location?: string;
  start_time: string;
  end_time: string;
  created_at: string;
  updated_at: string;
  team_name?: string;
}

// Attendance Types
export enum AttendanceStatus {
  PRESENT = 'present',
  ABSENT = 'absent',
  EXCUSED = 'excused',
  PENDING = 'pending',
}

export interface Attendance {
  id: number;
  player_id: number;
  game_id?: number;
  event_id?: number;
  status: AttendanceStatus;
  notes?: string;
  recorded_by?: number;
  recorded_at: string;
  player_name?: string;
  player_jersey?: number;
}

// News Types
export interface News {
  id: number;
  title: string;
  content: string;
  team_id?: number;
  author_id: number;
  is_published: boolean;
  published_at?: string;
  created_at: string;
  updated_at: string;
  author_name?: string;
  team_name?: string;
}

// API Response Types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

// Calendar Event (for calendar view)
export interface CalendarEvent {
  id: string;
  title: string;
  start: Date;
  end: Date;
  type: 'game' | 'event';
  location?: string;
  teamId: number;
}
