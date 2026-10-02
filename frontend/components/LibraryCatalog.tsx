"use client";
import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import type { LibraryIndex, LibraryItem, LibraryCoverage } from '../lib/api';
import { defaultFilters, Filters, filterReadings, groupWorks, levelLabel } from '../lib/libraryBrowse';

export default function LibraryCatalog({ library, coverage, busy, onChoose }: { library: LibraryIndex; coverage: LibraryCoverage; busy: boolean; onChoose: (i:LibraryItem)=>void }) {
  const [filters,setFilters]=useState<Filters>(defaultFilters);
  const [view,setView]=useState('works');
  const [page,setPage]=useState(0);
  useEffect(()=>{ const p=new URLSearchParams(location.search); const f={...defaultFilters}; (Object.keys(f) as (keyof Filters)[]).forEach(k=>{if(p.has(k))f[k]=p.get(k)!;});setFilters(f); },[]);
  function update(k:keyof Filters,v:string){const f={...filters,[k]:v};setFilters(f);setPage(0);const p=new URLSearchParams(location.search);(Object.keys(f) as (keyof Filters)[]).forEach(key=>{if(f[key] && f[key]!==defaultFilters[key])p.set(key,f[key]);else p.delete(key);});history.replaceState(null,'',location.pathname+(p.size?'?'+p:''));}
  function reset(){setFilters(defaultFilters);setPage(0);const p=new URLSearchParams(location.search);Object.keys(defaultFilters).forEach(k=>p.delete(k));history.replaceState(null,'',location.pathname+(p.size?'?'+p:''));}
  const results=useMemo(()=>filterReadings(library.items,filters,coverage),[library,filters,coverage]);
  const groups=useMemo(()=>groupWorks(results),[results]);
  const suggested=useMemo(()=>{
    const seen=new Set<string>();return filterReadings(library.items,defaultFilters,coverage).filter(i=>{const key=i.author+i.work;if(seen.has(key))return false;seen.add(key);return true;}).slice(0,3);
  },[library,coverage]);
  const size=view==='works'?8:20, total=view==='works'?groups.length:results.length;
  const currentPage=Math.min(page,Math.max(0,Math.ceil(total/size)-1));
  const active=Object.entries(filters).filter(([k,v])=>v && k!=='sort');
  function meta(i:LibraryItem){return `${levelLabel[i.level]??i.level} · ${i.dialect} · ${i.word_count} words`;}
  function passage(i:LibraryItem){return <li key={i.id}><button className="catalogPassage" disabled={busy} onClick={()=>onChoose(i)}><span><strong>{i.sequence ? `Section ${i.ref}` : i.title}</strong><small>{view==='passages'?`${i.author} · ${i.work} · `:''}{meta(i)}</small></span><span aria-hidden="true">Read →</span></button></li>;}
  return <div className="catalog">
    <div className="catalogIntro"><div><h2>Explore Greek literature</h2><p>{library.items.length} passages · {groupWorks(library.items).length} works · {new Set(library.items.map(i=>i.author)).size} authors</p></div><Link className="secondary" href="/library/new">Add your own text</Link></div>
    <section aria-labelledby="recommended-heading" className="catalogSuggestions"><h3 id="recommended-heading">Suggested starting points</h3><p className="muted">Shorter, easier original texts first. These are reading guides, not a personal proficiency assessment.</p><div className="suggestionGrid">{suggested.map(i=><button disabled={busy} className="suggestion" key={i.id} onClick={()=>onChoose(i)}><small>{i.author}</small><strong>{i.work}</strong><span>{i.title}</span><small>{meta(i)}</small><span className="suggestionReason">{coverage[i.id]?`${Math.round(coverage[i.id].coverage*100)}% matched by the app’s vocabulary lists`:'Accessible prose with reading tools'} · Read →</span></button>)}</div></section>
    <section className="catalogBrowse" aria-labelledby="browse-heading"><h2 id="browse-heading">Browse the collection</h2>
    <label className="catalogSearch">Search texts<input type="search" value={filters.query} placeholder="Author, work, topic, or passage…" onChange={e=>update('query',e.target.value)}/></label>
    <div className="catalogFilters">{([
      ['author','Author',[...new Set(library.items.map(i=>i.author))].sort().map(v=>[v,v])],
      ['category','Subject',library.categories.map(c=>[c.id,c.label])],
      ['level','Difficulty',Object.entries(levelLabel)],
      ['dialect','Dialect',[...new Set(library.items.map(i=>i.dialect))].sort().map(v=>[v,v])],
      ['length','Passage length',[['short','Up to 200 words'],['medium','201–400 words'],['long','Over 400 words']]],
    ] as [keyof Filters,string,string[][]][]).map(([key,label,options])=><label key={key}>{label}<select aria-label={label} value={filters[key]} onChange={e=>update(key,e.target.value)}><option value="">All</option>{options.map(([v,t])=><option value={v} key={v}>{t}</option>)}</select></label>)}</div>
    {active.length>0 && <div className="catalogChips">{active.map(([k,v])=><button key={k} className="secondary" onClick={()=>update(k as keyof Filters,'')}>{k==='query'?`“${v}”`:v} <span aria-label="remove">×</span></button>)}<button className="linkButton" onClick={reset}>Clear filters</button></div>}
    <div className="catalogToolbar"><p role="status">{results.length} passages in {groups.length} works</p><div className="catalogControls"><label>Sort<select aria-label="Sort" value={filters.sort} onChange={e=>update('sort',e.target.value)}><option value="recommended">Recommended</option><option value="author">Author A–Z</option><option value="title">Work A–Z</option><option value="shortest">Shortest passages</option><option value="support">Most vocabulary support</option></select></label><div className="tabs" role="group" aria-label="Display"><button className={`tab ${view==='works'?'on':''}`} aria-pressed={view==='works'} onClick={()=>{setView('works');setPage(0);}}>Works</button><button className={`tab ${view==='passages'?'on':''}`} aria-pressed={view==='passages'} onClick={()=>{setView('passages');setPage(0);}}>Passages</button></div></div></div>
    {total===0?<div className="catalogEmpty"><h3>No matching readings</h3><p>Try a different term or remove a filter.</p><button className="secondary" onClick={reset}>Clear filters</button></div>:view==='works'?<div className="catalogWorks">{groups.slice(currentPage*size,(currentPage+1)*size).map(({key,passages})=>{const i=passages.find(p=>p.sequence) ?? passages[0];return <details className="catalogWork" key={key}><summary><span className="workMonogram" aria-hidden="true">{i.author.slice(0,1)}</span><span className="workSummary"><small>{i.author} · {i.category}</small><strong>{i.work}</strong><span>{i.blurb}</span><small>{passages.length} matching passages · {i.dialect} · {levelLabel[i.level]??i.level}</small></span><span className="workExpand" aria-hidden="true">+</span></summary><ul className="catalogPassages">{passages.map(passage)}</ul></details>;})}</div>:<ul className="catalogPassages">{results.slice(currentPage*size,(currentPage+1)*size).map(passage)}</ul>}
    {total>size&&<nav className="catalogPagination" aria-label="Catalog pages"><button className="secondary" disabled={currentPage===0} onClick={()=>setPage(currentPage-1)}>Previous</button><span>Page {currentPage+1} of {Math.ceil(total/size)}</span><button className="secondary" disabled={(currentPage+1)*size>=total} onClick={()=>setPage(currentPage+1)}>Next</button></nav>}
    <p className="catalogNote">Difficulty is an editorial estimate relative to original Greek, not beginner course material. Vocabulary support measures dictionary matches, not words you personally know. Imported readings are opening selections, not complete books.</p>
    <p className="attribution">Greek texts from <a href="https://github.com/PerseusDL/canonical-greekLit" target="_blank" rel="noreferrer">Perseus Digital Library</a>, CC BY-SA 4.0. Edition and section links accompany each reading.</p>
    </section>
  </div>;
}
