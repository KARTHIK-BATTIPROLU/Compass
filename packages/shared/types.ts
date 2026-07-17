// Shared TypeScript definitions for LearnForge

export type Role = 'faculty' | 'learner';

export interface UserProfile {
  id: string;
  role: Role;
  name: string;
  email: string;
  region?: string;
  language?: string;
  standard?: string;
}
