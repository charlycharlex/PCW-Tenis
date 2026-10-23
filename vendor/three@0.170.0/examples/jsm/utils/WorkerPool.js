/**
 * Minified by jsDelivr using Terser v5.19.2.
 * Original file: /npm/three@0.170.0/examples/jsm/utils/WorkerPool.js
 *
 * Do NOT use SRI with dynamically generated files! More information: https://www.jsdelivr.com/using-sri-with-dynamic-files
 */
export class WorkerPool{constructor(e=4){this.pool=e,this.queue=[],this.workers=[],this.workersResolve=[],this.workerStatus=0}_initWorker(e){if(!this.workers[e]){const s=this.workerCreator();s.addEventListener("message",this._onMessage.bind(this,e)),this.workers[e]=s}}_getIdleWorker(){for(let e=0;e<this.pool;e++)if(!(this.workerStatus&1<<e))return e;return-1}_onMessage(e,s){const r=this.workersResolve[e];if(r&&r(s),this.queue.length){const{resolve:s,msg:r,transfer:t}=this.queue.shift();this.workersResolve[e]=s,this.workers[e].postMessage(r,t)}else this.workerStatus^=1<<e}setWorkerCreator(e){this.workerCreator=e}setWorkerLimit(e){this.pool=e}postMessage(e,s){return new Promise((r=>{const t=this._getIdleWorker();-1!==t?(this._initWorker(t),this.workerStatus|=1<<t,this.workersResolve[t]=r,this.workers[t].postMessage(e,s)):this.queue.push({resolve:r,msg:e,transfer:s})}))}dispose(){this.workers.forEach((e=>e.terminate())),this.workersResolve.length=0,this.workers.length=0,this.queue.length=0,this.workerStatus=0}}
//# sourceMappingURL=/sm/065c772ec369bd303d6d9df885f5592f4f91de9b753783bed032a0f6d928928d.map