import type { LibraryItem, LibraryCoverage } from './api';
export const levelLabel: Record<string,string> = { beginner: 'Easier original', intermediate: 'Intermediate', advanced: 'Advanced' };
export const normalizeSearch = (s: string) => s.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/ς/g,'σ');
export type Filters = { query: string; author: string; category: string; level: string; dialect: string; length: string; sort: string };
export const defaultFilters: Filters = { query:'',author:'',category:'',level:'',dialect:'',length:'',sort:'recommended' };
export function readingScore(item: LibraryItem, coverage: LibraryCoverage) {
  return ({beginner: 0, intermediate: 100, advanced: 200}[item.level] ?? 200) + (1-(coverage[item.id]?.coverage ?? 0))*35 + Math.min(item.estimated_seconds/60,20) + (item.sequence ? 8 : 0);
}
export function filterReadings(items: LibraryItem[], f: Filters, coverage: LibraryCoverage) {
  const q = normalizeSearch(f.query.trim());
  return items.filter(i => (!q || normalizeSearch([i.title,i.author,i.work,i.ref,i.blurb].join(' ')).includes(q)) && (!f.author || i.author===f.author) && (!f.category || i.category===f.category) && (!f.level || i.level===f.level) && (!f.dialect || i.dialect===f.dialect) && (!f.length || (f.length==='short' ? i.word_count<=200 : f.length==='medium' ? i.word_count>200 && i.word_count<=400 : i.word_count>400))).sort((a,b) => {
    if(f.sort==='author') return a.author.localeCompare(b.author) || a.work.localeCompare(b.work) || (a.sequence??0)-(b.sequence??0);
    if(f.sort==='title') return a.work.localeCompare(b.work) || a.author.localeCompare(b.author) || (a.sequence??0)-(b.sequence??0);
    if(f.sort==='shortest') return a.word_count-b.word_count;
    if(f.sort==='support') return (coverage[b.id]?.coverage??-1)-(coverage[a.id]?.coverage??-1);
    return readingScore(a,coverage)-readingScore(b,coverage);
  });
}
export function groupWorks(items: LibraryItem[]) {
  const map=new Map<string,LibraryItem[]>();
  items.forEach(i=>{const key=i.author+' / '+i.work;map.set(key,[...(map.get(key)??[]),i]);});
  return [...map.entries()].map(([key,passages])=>({key,passages:passages.sort((a,b)=>(a.sequence??0)-(b.sequence??0))}));
}
