// User Types
export enum UserRole {
  ADMIN = 'admin',
  COACH = 'coach',
  SUPERVISOR = 'supervisor',
  PLAYER = 'player',
  PARENT = 'parent',
}

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  phone?: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
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
  user?: User;
}

// OAuth Types
export interface OAuthLoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user_id: string;
  email: string;
  role: UserRole;
  first_name: string;
  last_name: string;
  is_new_user: boolean;
  needs_role_selection: boolean;
}

// Team Types
export interface Team {
  id: string;
  name: string;
  description?: string;
  age_group?: string;
  coach_id?: string;
  supervisor_id?: string;
  created_at: string;
  updated_at?: string;
  player_count?: number;
  coach_name?: string;
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

export const PositionLabels: Record<Position, string> = {
  [Position.GOALKEEPER]: 'Torwart',
  [Position.LEFT_WING]: 'Linksaußen',
  [Position.LEFT_BACK]: 'Rückraum Links',
  [Position.CENTER_BACK]: 'Rückraum Mitte',
  [Position.RIGHT_BACK]: 'Rückraum Rechts',
  [Position.RIGHT_WING]: 'Rechtsaußen',
  [Position.PIVOT]: 'Kreisläufer',
  [Position.DEFENSE]: 'Defensiv',
};

export interface Player {
  id: string;
  user_id?: string;
  user?: User;
  team_id?: string;
  team_name?: string;
  jersey_number?: number;
  position?: Position;
  date_of_birth?: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  games_played: number;
  goals_scored: number;
  assists?: number;
  parent_ids?: string[];
  parents?: ParentInfo[];
  created_at?: string;
  updated_at?: string;
  joined_date?: string;
  birth_date?: string;
  emergency_contact?: string;
}

// Parent-Child Relationship
export interface ParentChildRelationship {
  id: string;
  parent_id: string;
  player_id: string;
  created_at: string;
}

export interface ParentInfo {
  id: string;
  first_name: string;
  last_name: string;
  email?: string;
  phone?: string;
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
  id: string;
  team_id: string;
  team_name?: string;
  opponent: string;
  opponent_logo?: string | null;
  location: string;
  scheduled_at: string;
  game_type?: GameType;
  status: GameStatus;
  home_score?: number | null;
  away_score?: number | null;
  is_home_game?: boolean;
  notes?: string;
  created_at?: string;
  updated_at?: string;
}

// Event Types with Visibility
export enum EventType {
  TRAINING = 'training',
  MEETING = 'meeting',
  TOURNAMENT = 'tournament',
  OTHER = 'other',
}

export enum EventVisibility {
  TEAM = 'team',
  CLUB = 'club',
  AGE_GROUP = 'age_group',
  PRIVATE = 'private',
}

export const EventTypeLabels: Record<EventType, string> = {
  [EventType.TRAINING]: 'Training',
  [EventType.MEETING]: 'Besprechung',
  [EventType.TOURNAMENT]: 'Turnier',
  [EventType.OTHER]: 'Sonstiges',
};

export const EventVisibilityLabels: Record<EventVisibility, string> = {
  [EventVisibility.TEAM]: 'Mannschaft',
  [EventVisibility.CLUB]: 'Verein',
  [EventVisibility.AGE_GROUP]: 'Altersklasse',
  [EventVisibility.PRIVATE]: 'Privat',
};

export interface Event {
  id: string;
  title: string;
  description?: string;
  team_id?: string | null;
  team_name?: string;
  event_type: EventType;
  visibility: EventVisibility;
  age_group?: string;
  location?: string;
  start_time: string;
  end_time: string;
  created_by?: string;
  created_at?: string;
  updated_at?: string;
}

// Attendance Types
export enum AttendanceStatus {
  PRESENT = 'present',
  ABSENT = 'absent',
  EXCUSED = 'excused',
  PENDING = 'pending',
}

export const AttendanceStatusLabels: Record<AttendanceStatus, string> = {
  [AttendanceStatus.PRESENT]: 'Anwesend',
  [AttendanceStatus.ABSENT]: 'Abwesend',
  [AttendanceStatus.EXCUSED]: 'Entschuldigt',
  [AttendanceStatus.PENDING]: 'Ausstehend',
};

export interface Attendance {
  id: string;
  player_id: string;
  player_name?: string;
  player_jersey?: number;
  game_id?: string;
  event_id?: string;
  event_name?: string;
  status: AttendanceStatus;
  notes?: string;
  recorded_by?: string;
  recorded_at: string;
}

// News Types
export interface News {
  id: string;
  title: string;
  content: string;
  team_id?: string | null;
  author_id?: string;
  is_published?: boolean;
  published_at?: string;
  created_at: string;
  updated_at?: string;
  author_name?: string;
  team_name?: string;
}

// Invitation Types
export interface Invitation {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  invited_by: string;
  team_id?: string;
  status: 'pending' | 'accepted' | 'expired';
  created_at: string;
  expires_at: string;
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
  teamId?: string;
}

// Notification Types
export interface AppNotification {
  id: string;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  read: boolean;
  created_at: string;
  user_id?: string;
  link?: string;
}

// Form Types
export interface PlayerCreationForm {
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  date_of_birth?: string;
  jersey_number?: number;
  position?: Position;
  team_id?: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  parent_ids?: string[];
}

export interface ParentAssignmentForm {
  player_id: string;
  parent_id?: string;
  new_parent?: {
    first_name: string;
    last_name: string;
    email: string;
    phone?: string;
  };
}

export interface EventCreationForm {
  title: string;
  description?: string;
  event_type: EventType;
  visibility: EventVisibility;
  team_id?: string;
  age_group?: string;
  location?: string;
  start_time: string;
  end_time: string;
}
