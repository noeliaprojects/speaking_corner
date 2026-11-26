/* Speaking Corner: offline-friendly, small cache, automatic updates. */
const CORE="sc-core-v2",PHOTO="sc-images-v1";
const BASE="/speaking_corner/";
const SHELL=[BASE,BASE+"index.html",BASE+"src/my_activities.js",BASE+"manifest.webmanifest",BASE+"icons/app-192.png",BASE+"icons/app-512.png"];
self.addEventListener("install",event=>{
  event.waitUntil(caches.open(CORE).then(cache=>cache.addAll(SHELL.map(u=>new Request(u,{cache:"reload"})))).then(()=>self.skipWaiting()));
});
self.addEventListener("activate",event=>{
  event.waitUntil(Promise.all([
    caches.keys().then(keys=>Promise.all(keys.filter(k=>![CORE,PHOTO].includes(k)).map(k=>caches.delete(k)))),
    self.clients.claim()
  ]));
});
self.addEventListener("fetch",event=>{
  const req=event.request;
  if(req.method!=="GET"||new URL(req.url).origin!==self.location.origin)return;
  const url=new URL(req.url),isImage=url.pathname.includes(BASE+"img/");
  if(isImage){
    event.respondWith(caches.open(PHOTO).then(async cache=>{
      const saved=await cache.match(req);
      if(saved)return saved;
      const res=await fetch(req);
      if(res.ok){
        cache.put(req,res.clone());
        const keys=await cache.keys();
        if(keys.length>120)await cache.delete(keys[0]);
      }
      return res;
    }));
    return;
  }
  // Network first ensures newer activities and design are picked up when online.
  if(req.mode==="navigate"){
    event.respondWith(fetch(req,{cache:"no-cache"}).then(async res=>{
      if(res.ok){const cache=await caches.open(CORE);cache.put(BASE,res.clone());}
      return res;
    }).catch(async()=>(await caches.open(CORE)).match(BASE)||Response.error()));
    return;
  }
  if(url.pathname.startsWith(BASE)){
    event.respondWith(fetch(req,{cache:"no-cache"}).then(async res=>{
      if(res.ok&&(SHELL.some(p=>url.pathname===p))){const cache=await caches.open(CORE);cache.put(req,res.clone());}
      return res;
    }).catch(async()=>(await caches.open(CORE)).match(req)||Response.error()));
  }
});
