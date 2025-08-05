export type Player = {
  player_id: string;
  name: string;
  pos: 'QB' | 'RB' | 'WR' | 'TE' | 'K' | 'DST';
  tm: string;
  points: number;
  vorp: number;
  pos_rank: number;
  overall_rank: number;
  tier: number;
  repl_pts: number;
  bye?: number;
  ppg?: number;
  gp?: number;
  stdev?: number;
  p10_share?: number;
  p15_share?: number;
  p20_share?: number;
  round_est?: number;
  pick_in_round?: number;
  source?: 'blend' | 'override';
}

export type Meta = {
  generated_at?: string;
  target_year?: number;
  lookback_years?: number[];
  blend?: number[];
  per_game?: boolean;
  min_games?: number;
  schema_version?: string;
}
