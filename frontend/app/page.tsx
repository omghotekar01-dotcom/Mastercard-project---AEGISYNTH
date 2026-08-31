"use client";
import {useState} from "react";
import {Activity, BrainCircuit, CheckCircle2, FlaskConical, Play, ShieldCheck, Sparkles, TriangleAlert} from "lucide-react";
import {LabResult, runLab} from "../lib/api";

const pct=(n:number)=>`${(n*100).toFixed(1)}%`;
export default function Home(){
  const [data,setData]=useState<LabResult|null>(null);
  const [running,setRunning]=useState(false);
  const [error,setError]=useState("");
  async function launch(){
    setRunning(true);setError("");
    try{setData(await runLab(Math.floor(Math.random()*100000)));}catch(e){setError(e instanceof Error?e.message:"Unknown error");}
    finally{setRunning(false);}
  }
  return <main>
    <header className="nav"><div className="brand"><ShieldCheck size={27}/><b>AEGISYNTH</b><span>DEFENCE COMPILER</span></div><div className="status"><i/> SYNTHETIC LAB • SAFE MODE</div></header>
    <section className="hero">
      <div className="eyebrow"><Sparkles size={15}/> Mastercard AI Defence Lab • GFF 2026</div>
      <h1>Turn tomorrow&apos;s fraud into<br/><em>verified defence.</em></h1>
      <p>AEGISYNTH converts a novel payment attack into a compact, explainable policy by red-teaming candidates, feeding bypasses back as counterexamples, and formally checking safety constraints before deployment.</p>
      <div className="actions"><button onClick={launch} disabled={running}><Play size={18}/>{running?"Running adversarial lab…":"Release zero-day simulation"}</button><span>No real cards • No real merchants • No paid API required</span></div>
    </section>
    <section className="pipeline">
      {[ [FlaskConical,"01","SIMULATE","Synthetic attack family"], [BrainCircuit,"02","SYNTHESIZE","Compile minimal control"], [TriangleAlert,"03","COUNTEREXAMPLE","Mutate to find bypasses"], [ShieldCheck,"04","VERIFY","Safety + business constraints"] ].map(([Icon,n,t,d]:any)=><div className="step" key={n}><Icon size={20}/><small>{n}</small><b>{t}</b><span>{d}</span></div>)}
    </section>
    {error&&<div className="error">{error}</div>}
    {!data?<section className="empty"><Activity size={34}/><h2>Live adversarial lab is ready.</h2><p>Launch a safe synthetic zero-day to watch AEGISYNTH compile and verify a defence package.</p></section>:
    <>
      <section className="metrics">
        <Metric label="Baseline attack success" value={pct(data.baseline_attack_success_rate)} />
        <Metric label="After compilation" value={pct(data.final_attack_success_rate)} strong />
        <Metric label="Benign acceptance" value={pct(data.metrics.benign_acceptance_rate)} />
        <Metric label="Policy latency" value={`${data.metrics.estimated_policy_latency_ms.toFixed(2)} ms`} />
      </section>
      <section className="grid">
        <div className="panel"><div className="panelTitle"><span>ADVERSARIAL EVOLUTION</span><b>{data.attack_family.replaceAll("_"," ")}</b></div>
          <div className="bars">{data.iterations.map(it=><div className="barRow" key={it.iteration}><span>GEN {it.iteration}</span><div><i style={{width:`${it.attack_success_rate*100}%`}}/></div><b>{pct(it.attack_success_rate)}</b><small>{it.counterexamples} bypasses</small></div>)}</div>
        </div>
        <div className="panel policy"><div className="panelTitle"><span>COMPILED DEFENCE PACKAGE</span><b>{data.final_policy.policy_id}</b></div>
          <div className="verified"><CheckCircle2/> FORMALLY VERIFIED</div>
          <pre>{`IF merchant_age ≤ ${data.final_policy.merchant_age_max}h\nAND first_time_card_ratio ≥ ${data.final_policy.first_time_card_ratio_min}\nAND settlement_change ≤ ${data.final_policy.settlement_change_days_max}d\nAND temporal_burst ≥ ${data.final_policy.temporal_burst_score_min}\nTHEN ${data.final_policy.action}`}</pre>
          <p>{data.final_policy.explanation}</p>
        </div>
      </section>
      <section className="verify"><h3>Verification ledger</h3>{data.verification_notes.map(n=><div key={n}><CheckCircle2 size={16}/>{n}</div>)}</section>
    </>}
    <footer><b>AEGISYNTH</b><span>Attack → Counterexample → Synthesis → Verification → Defence</span></footer>
  </main>
}
function Metric({label,value,strong=false}:{label:string,value:string,strong?:boolean}){return <div className={strong?"metric strong":"metric"}><span>{label}</span><b>{value}</b></div>}
