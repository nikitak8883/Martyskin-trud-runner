export type AudioBus = 'UI'|'SFX'|'MonkeyVoice'|'Ambience'|'Music';
export interface AudioEventDefinition { eventId:string; bus:AudioBus; asset:string; cooldownMs:number; priority:number; maxSimultaneous:number; }
export interface AudioBackend { play(def:AudioEventDefinition):void; }
export class AudioEventRouter {
  private readonly lastPlayed=new Map<string,number>();
  constructor(private readonly defs:Map<string,AudioEventDefinition>, private readonly backend:AudioBackend){}
  emit(eventId:string, nowMs=Date.now()):boolean { const d=this.defs.get(eventId); if(!d) return false; const last=this.lastPlayed.get(eventId)??-Infinity; if(nowMs-last<d.cooldownMs) return false; this.lastPlayed.set(eventId,nowMs); this.backend.play(d); return true; }
}
