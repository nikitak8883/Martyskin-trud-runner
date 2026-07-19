export interface SaveEnvelope<T> { saveSchemaVersion:number; profileId:string; updatedAt:string; payload:T; checksum?:string; }
export interface KeyValueStore { get(key:string):string|null; set(key:string,value:string):void; remove(key:string):void; }
export type Migration<T>=(oldValue:unknown)=>T;
export class SaveRepository<T> {
  constructor(private readonly store:KeyValueStore, private readonly key:string, private readonly currentVersion:number, private readonly migrate:Migration<T>, private readonly makeDefault:()=>T){}
  load(profileId:string):SaveEnvelope<T>{ const raw=this.store.get(`${this.key}:${profileId}`); if(!raw) return this.wrap(profileId,this.makeDefault()); try { const parsed=JSON.parse(raw); const payload=parsed.saveSchemaVersion===this.currentVersion?parsed.payload:this.migrate(parsed); return this.wrap(profileId,payload); } catch { return this.wrap(profileId,this.makeDefault()); } }
  save(value:SaveEnvelope<T>):void{ this.store.set(`${this.key}:${value.profileId}`,JSON.stringify({...value,updatedAt:new Date().toISOString()})); }
  private wrap(profileId:string,payload:T):SaveEnvelope<T>{ return {saveSchemaVersion:this.currentVersion,profileId,updatedAt:new Date().toISOString(),payload}; }
}
