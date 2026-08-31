export type Policy = {
  policy_id:string; merchant_age_max:number; first_time_card_ratio_min:number;
  settlement_change_days_max:number; temporal_burst_score_min:number;
  action:string; fraud_coverage:number; false_positive_rate:number;
  estimated_latency_ms:number; counterexamples_remaining:number; verified:boolean; explanation:string;
};
export type Iteration = {iteration:number; candidate:Policy; counterexamples:number; attack_success_rate:number};
export type LabResult = {
  attack_family:string; seed:number; baseline_attack_success_rate:number; final_attack_success_rate:number;
  iterations:Iteration[]; final_policy:Policy; verification_notes:string[]; metrics:Record<string,number>;
};
export async function runLab(seed:number):Promise<LabResult>{
  const base = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const res = await fetch(`${base}/api/v1/lab/run?seed=${seed}&generations=4`, {cache:"no-store"});
  if(!res.ok) throw new Error(`Lab failed: ${res.status}`);
  return res.json();
}
