/* Speaking Corner: private activities and PDF library (browser-only). */
const MY=(function makeMyActivities(){
  const KEY="sc-my-activities",PDF_DB="speaking-corner-private-pdfs",PDF_STORE="files";
  const fmtTypes={all:["ind","pair","grp"],ind:["ind"],pair:["pair"],grp:["grp"]};
  const all=()=>{const v=store.get(KEY,[]);return Array.isArray(v)?v:[];};
  const saveAll=items=>store.set(KEY,items);
  const get=id=>all().find(a=>a.id===id)||null;
  const unique=()=>`mine-${Date.now().toString(36)}-${Math.random().toString(36).slice(2,8)}`;
  const levels=["A1","A2","B1","B2","C1"];
  const fmtKey=a=>Object.entries(fmtTypes).find(([_,v])=>JSON.stringify(v)===JSON.stringify(a.fmts))?.[0]||"all";
  function deck(id){
    const r=get(id);
    if(!r)return null;
    const base={id:r.id,name:r.name,cat:"mine",lv:r.lv||["B1"],fmts:r.fmts||fmtTypes.all,
      ages:["9-12","12-14","14-16","16-18","19-25","adults"],gram:[],desc:r.desc||"",mine:true};
    if(r.type==="pdf")return {...base,minePdf:true,kind:"pdf",instr:r.instr||""};
    return {...base,kind:"single",instr:r.instr||"Discuss each prompt and explain your answer.",
      ph:r.ph||[],cards:r.cards||[],end:"Share your most interesting answer."};
  }
  const deckEntries=()=>all().map(r=>deck(r.id)).filter(Boolean);
  function openDb(){
    if(!window.indexedDB)return Promise.reject(new Error("This browser does not support local PDF storage."));
    return new Promise((resolve,reject)=>{
      const req=indexedDB.open(PDF_DB,1);
      req.onupgradeneeded=()=>{const db=req.result;if(!db.objectStoreNames.contains(PDF_STORE))db.createObjectStore(PDF_STORE);};
      req.onsuccess=()=>resolve(req.result);req.onerror=()=>reject(req.error||new Error("Unable to open PDF storage."));
    });
  }
  async function pdfAction(id,kind,file){
    const db=await openDb();
    return new Promise((resolve,reject)=>{
      const tx=db.transaction(PDF_STORE,kind==="get"?"readonly":"readwrite"),os=tx.objectStore(PDF_STORE);
      let result;
      const request=kind==="put"?os.put(file,id):kind==="delete"?os.delete(id):os.get(id);
      request.onsuccess=()=>{result=request.result;};
      tx.oncomplete=()=>{db.close();resolve(result);};
      tx.onerror=()=>{db.close();reject(tx.error||new Error("Cannot access this PDF on the current device."));};
      tx.onabort=()=>{db.close();reject(tx.error||new Error("PDF operation was cancelled."));};
    });
  }
  async function openPdf(id,statusId){
    const tab=window.open("","_blank");
    try{
      const file=await pdfAction(id,"get");
      if(!file){if(tab)tab.close();throw new Error("The PDF is not on this device. Edit the activity and attach the PDF again.");}
      const url=URL.createObjectURL(file);
      if(tab)tab.location.href=url;
      else {const a=document.createElement("a");a.href=url;a.download=(get(id)?.name||"Activity")+".pdf";document.body.appendChild(a);a.click();a.remove();}
      setTimeout(()=>URL.revokeObjectURL(url),120000);
    }catch(e){if(tab)tab.close();const status=document.getElementById(statusId);if(status)status.textContent=e.message||"Unable to open PDF.";else alert(e.message);}
  }
  const rows=()=>all().slice().sort((a,b)=>(b.updated||0)-(a.updated||0));
  function view(editId){
    const edit=get(editId),isCards=edit?.type==="cards",isPdf=edit?.type==="pdf";
    app.innerHTML=`<div class="narrow my-activities">
      <div class="top"><a class="back" href="#">← All activities</a><a class="back" href="#plans">My lesson plans</a></div>
      <h1>My <span>activities</span></h1>
      <p class="sub">Keep your own speaking cards and PDFs together, ready to use in class or add to a lesson plan.</p>
      <section class="card"><div class="row" style="justify-content:space-between">
        <h2>Saved activities <span class="note">${all().length}</span></h2><a class="btn ghost" href="#my-activities">+ New activity</a></div>
        ${all().length?`<div class="lp-list">${rows().map(a=>`<div class="lp-summary my-summary">
          <span><strong>${esc(a.name)}</strong><small>${a.type==="pdf"?"PDF":"Speaking cards"} · ${esc((a.lv||["B1"]).join(", "))} · ${esc(a.desc||"Your activity")}</small></span>
          <div class="my-buttons"><a class="btn ghost" href="#mine/${esc(a.id)}">Open</a>
          <button type="button" class="ghost" data-my-edit="${esc(a.id)}">Edit</button>
          <button type="button" class="ghost" data-my-add="${esc(a.id)}">+ Lesson</button>
          <button type="button" class="ghost" data-my-delete="${esc(a.id)}">Delete</button></div></div>`).join("")}</div>`:
          `<p class="note">You haven't added anything yet. Create a speaking activity or attach a PDF below.</p>`}
      </section>
      <section class="card lp-compact" id="myForm">
       <h2>${edit?"Edit activity":"Add an activity"}</h2>
       <div class="row"><label class="field"><span class="label">Activity type</span><select id="myType" ${edit?"disabled":""}>
         <option value="cards" ${!isPdf?"selected":""}>Create speaking cards</option>
         <option value="pdf" ${isPdf?"selected":""}>Upload a PDF</option></select></label>
         <label class="field"><span class="label">Level</span><select id="myLevel">${levels.map(x=>`<option ${edit?.lv?.includes(x)?"selected":(!edit?.lv?.length&&x==="B1"?"selected":"")}>${x}</option>`).join("")}</select></label></div>
       <label class="field"><span class="label">Name</span><input id="myName" value="${esc(edit?.name||"")}" maxlength="100" placeholder="e.g. Mystery Guest"></label>
       <label class="field"><span class="label">Description</span><input id="myDesc" value="${esc(edit?.desc||"")}" maxlength="190" placeholder="What will your students do?"></label>
       <label class="field"><span class="label">Format</span><select id="myFmt">
          ${[["all","Any format"],["ind","Individual"],["pair","Pairs"],["grp","Whole group"]].map(([v,t])=>`<option value="${v}" ${fmtKey(edit||{fmts:fmtTypes.all})===v?"selected":""}>${t}</option>`).join("")}</select></label>
       <div id="myCardsFields">
         <label class="field"><span class="label">Instructions for students</span><textarea id="myInstr" rows="2" placeholder="Choose a card and explain your answer.">${esc(edit?.instr||"")}</textarea></label>
         <label class="field"><span class="label">Cards — one prompt per line</span><textarea id="myCards" rows="8" placeholder="What would you do if…?&#10;Which would you choose, and why?">${esc(isCards?(edit.cards||[]).join("\n"):"")}</textarea></label>
         <label class="field"><span class="label">Useful language — one phrase per line (optional)</span><textarea id="myPhrases" rows="4" placeholder="In my opinion…&#10;On the other hand…">${esc(isCards?(edit.ph||[]).join("\n"):"")}</textarea></label>
       </div>
       <div id="myPdfFields" hidden>
         <label class="field"><span class="label">PDF file ${isPdf?"(optional when editing)":"(required)"}</span><input id="myFile" type="file" accept=".pdf,application/pdf"></label>
         <p class="note">PDFs are kept privately in this browser, not uploaded to the public website. Maximum 25 MB per file.</p>
       </div>
       <div class="row"><button class="primary" id="mySave" type="button">${edit?"Save changes":"+ Save activity"}</button>
        ${edit?`<a class="btn ghost" href="#my-activities">Cancel edit</a>`:""}</div>
       <p id="myStatus" class="note" role="status"></p>
      </section>
      <p class="note">Your activities are private to this browser. The My classes backup includes card activities and PDF information, but <b>not the PDF files themselves</b>; keep the original PDFs when moving devices.</p>
    </div>`;
    const kind=$("#myType"),cardsFields=$("#myCardsFields"),pdfFields=$("#myPdfFields");
    const showKind=()=>{cardsFields.hidden=kind.value!=="cards";pdfFields.hidden=kind.value!=="pdf";};
    kind.onchange=showKind;showKind();
    if(edit){document.querySelector("#myForm")?.scrollIntoView({block:"nearest"});}
    app.querySelectorAll("[data-my-edit]").forEach(b=>b.onclick=()=>view(b.dataset.myEdit));
    app.querySelectorAll("[data-my-add]").forEach(b=>b.onclick=()=>LP.choose(b.dataset.myAdd));
    app.querySelectorAll("[data-my-delete]").forEach(b=>b.onclick=async()=>{
      if(!b.dataset.confirm){b.dataset.confirm="1";b.textContent="Confirm delete";return;}
      const id=b.dataset.myDelete,r=get(id);
      if(r?.type==="pdf"){try{await pdfAction(id,"delete");}catch(e){}}
      saveAll(all().filter(a=>a.id!==id));view();
    });
    $("#mySave").onclick=async()=>{
      const status=$("#myStatus"),name=$("#myName").value.trim(),type=kind.value,desc=$("#myDesc").value.trim();
      if(!name){status.textContent="Please give this activity a name.";$("#myName").focus();return;}
      const lv=[$("#myLevel").value],fmts=fmtTypes[$("#myFmt").value]||fmtTypes.all;
      const id=edit?.id||unique(),common={id,name:name.slice(0,100),desc:desc.slice(0,190),lv,fmts,type,updated:Date.now()};
      if(type==="cards"){
        const split=id=>id.split(/\r?\n/).map(x=>x.trim()).filter(Boolean);
        const cards=split($("#myCards").value).slice(0,50).map(x=>x.slice(0,400));
        const ph=split($("#myPhrases").value).slice(0,20).map(x=>x.slice(0,180));
        if(!cards.length){status.textContent="Please add at least one speaking card.";$("#myCards").focus();return;}
        const instr=$("#myInstr").value.trim().slice(0,400)||"Discuss each prompt and explain your answer.";
        const record={...common,cards,ph,instr};
        saveAll([...all().filter(x=>x.id!==id),record]);location.hash="mine/"+id;return;
      }
      const file=$("#myFile").files[0];
      if(!file&&!isPdf){status.textContent="Choose a PDF file to upload.";return;}
      if(file){
        if((file.type&&file.type!=="application/pdf")&&!file.name.toLowerCase().endsWith(".pdf")){status.textContent="Please select a PDF file.";return;}
        if(file.size>25*1024*1024){status.textContent="The PDF must be smaller than 25 MB.";return;}
        status.textContent="Saving PDF to this browser…";
        try{await pdfAction(id,"put",file);}
        catch(e){status.textContent="Could not store the PDF: "+e.message;return;}
      }
      saveAll([...all().filter(x=>x.id!==id),{...common,type:"pdf",fileName:file?.name||edit?.fileName||""}]);
      location.hash="mine/"+id;
    };
  }
  function pdfView(id){
    const r=get(id);if(!r||r.type!=="pdf"){location.hash="my-activities";return;}
    const current=CL.active();
    const done=!!(current&&H.dates(current.id,id).includes(today()));
    app.innerHTML=`<div class="narrow">
      <div class="top"><a class="back" href="#my-activities">← My activities</a>${classSwitcher()}</div>
      <h1>${esc(r.name)}</h1><p class="sub">${esc(r.desc||"Your PDF activity")} · ${esc((r.lv||[]).join(", "))}</p>
      <section class="card"><h2>Your PDF</h2>
        <p class="note">This PDF is stored on your device, not on the public site.</p>
        <div class="row"><button class="primary" id="myOpenPdf">Open PDF</button>
          <button class="ghost" id="myPdfLesson">+ Add to lesson</button>
          <a class="btn ghost" href="#my-activities">Edit or replace PDF</a></div>
        <p id="myPdfMessage" class="note" role="status"></p>
      </section>
      <section class="card"><h2>Class history</h2><p class="note">${current?esc(current.name):"Choose a class to track completed activities."}</p>
        ${current?`<button class="${done?"ghost":"primary"}" id="myPdfDone">${done?"Marked as done":"Mark as done"}</button>`:""}
      </section></div>`;
    $("#myOpenPdf").onclick=()=>openPdf(id,"myPdfMessage");
    $("#myPdfLesson").onclick=()=>LP.choose(id);
    if($("#myPdfDone"))$("#myPdfDone").onclick=()=>{if(!done&&current)H.mark(current.id,id);pdfView(id);};
    wireClassSwitcher(()=>pdfView(id));
  }
  function importRecords(raw){
    if(!Array.isArray(raw))return;
    const existing=all(),known=new Set(existing.map(x=>x.id));
    for(const r of raw){
      if(!r||typeof r!=="object"||!/^mine-[a-z0-9-]+$/.test(String(r.id))||known.has(r.id)||!["cards","pdf"].includes(r.type))continue;
      const safe={id:r.id,type:r.type,name:String(r.name||"Imported activity").slice(0,100),
        desc:String(r.desc||"").slice(0,190),lv:Array.isArray(r.lv)?r.lv.filter(x=>levels.includes(x)).slice(0,1):["B1"],
        fmts:Array.isArray(r.fmts)?r.fmts.filter(x=>["ind","pair","grp"].includes(x)):fmtTypes.all,updated:Date.now()};
      if(!safe.lv.length)safe.lv=["B1"];
      if(!safe.fmts.length)safe.fmts=fmtTypes.all;
      if(safe.type==="cards"){
        safe.cards=Array.isArray(r.cards)?r.cards.map(x=>String(x).slice(0,400)).filter(Boolean).slice(0,50):[];
        if(!safe.cards.length)continue;
        safe.ph=Array.isArray(r.ph)?r.ph.map(x=>String(x).slice(0,180)).filter(Boolean).slice(0,20):[];
        safe.instr=String(r.instr||"Discuss each card.").slice(0,400);
      }else safe.fileName=String(r.fileName||"").slice(0,150);
      existing.push(safe);known.add(safe.id);
    }
    saveAll(existing);
  }
  return {all,get,deck,deckEntries,view,pdfView,importRecords};
})();
