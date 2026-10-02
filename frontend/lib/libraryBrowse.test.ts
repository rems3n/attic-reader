import { describe, it, expect } from 'vitest';
import { defaultFilters, filterReadings, groupWorks, normalizeSearch } from './libraryBrowse';
import type { LibraryItem } from './api';
const item=(id:string,overrides:Partial<LibraryItem>={}):LibraryItem=>({id,author:'Xenophon',work:'Memorabilia',title:'Socrates',category:'philosophy',level:'intermediate',dialect:'attic',ref:'1.1',blurb:'Virtue',word_count:180,sentence_count:9,estimated_seconds:80,ready_speeds:[],source:{edition:'Perseus',urn:'urn:x',license:'CC BY-SA 4.0',url:'https://example.com'},...overrides});
describe('reading catalog',()=>{
 it('combines filters and ignores accents in searches',()=>{const a=item('a',{title:'Σωκράτης'});expect(normalizeSearch('Σωκράτης')).toBe(normalizeSearch('σωκρατησ'));expect(filterReadings([a,item('b',{author:'Plato'})],{...defaultFilters,query:'σωκρατης',author:'Xenophon',length:'short'},{})).toEqual([a]);});
 it('keeps same-name works by different authors separate and sequences in order',()=>{const groups=groupWorks([item('b',{sequence:2}),item('a',{sequence:1}),item('c',{author:'Plato'})]);expect(groups).toHaveLength(2);expect(groups[0].passages.map(i=>i.id)).toEqual(['a','b']);});
 it('orders support by actual coverage, with missing coverage last',()=>{expect(filterReadings([item('a'),item('b'),item('c')],{...defaultFilters,sort:'support'},{b:{coverage:.9,dcc_coverage:.9,words:20,unknown:2},a:{coverage:.2,dcc_coverage:.2,words:20,unknown:16}}).map(i=>i.id)).toEqual(['b','a','c']);});
 it('filters length boundaries and sorts shortest first',()=>{const items=[item('a',{word_count:201}),item('b',{word_count:400}),item('c',{word_count:401})];expect(filterReadings(items,{...defaultFilters,length:'medium',sort:'shortest'},{}).map(i=>i.id)).toEqual(['a','b']);});
});
