"""Rebuild opening reading sequences from a local Perseus canonical-greekLit checkout.
Usage: python scripts/expand_library.py /path/to/canonical-greekLit
Preserves the twelve original featured readings. Imports complete TEI sections,
not generated paraphrases; records source commit and exact section references.
"""
import json
import sys
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from build_library import DATA_DIR, TEI, element_text, build_passage

# Author, work number, title, subject, level, dialect, reading context.
WORKS = [
('0032','001','Hellenica','history','intermediate','attic','The closing years of the Peloponnesian War and the history that follows.'),
('0032','002','Memorabilia','philosophy','intermediate','attic','Socrates in conversation about conduct, education, and virtue.'),
('0032','003','Oeconomicus','philosophy','intermediate','attic','Socrates discusses household management, property, and practical knowledge.'),
('0032','004','Symposium','philosophy','intermediate','attic','Conversation at a banquet, with reflections on love and character.'),
('0032','005','Apology','philosophy','intermediate','attic','Xenophon’s account of Socrates’ defence and attitude toward death.'),
('0032','006','Anabasis','history','beginner','attic','Narrative prose about Cyrus’ expedition and the Greek soldiers’ return.'),
('0032','007','Cyropaedia','history','intermediate','attic','Cyrus’ upbringing and leadership, told through narrative and dialogue.'),
('0032','008','Hiero','politics','intermediate','attic','A conversation about tyranny, power, and happiness.'),
('0032','010','Constitution of the Lacedaemonians','politics','intermediate','attic','Spartan education, customs, and political institutions.'),
('0032','013','On Horsemanship','practical','intermediate','attic','Practical prose on selecting, caring for, and riding horses.'),
('0059','001','Euthyphro','philosophy','intermediate','attic','Socrates asks what piety means through questions and definitions.'),
('0059','002','Apology','philosophy','intermediate','attic','Socrates addresses the jury at his trial.'),
('0059','003','Crito','philosophy','beginner','attic','Socrates and Crito discuss escape, justice, and obligation to the laws.'),
('0059','004','Phaedo','philosophy','advanced','attic','The final conversation of Socrates, on the soul and death.'),
('0059','011','Symposium','philosophy','advanced','attic','Speeches about the nature of love at an Athenian banquet.'),
('0059','019','Laches','philosophy','intermediate','attic','A dialogue about courage and the education of young men.'),
('0059','024','Meno','philosophy','intermediate','attic','Questions about virtue, learning, and whether virtue can be taught.'),
('0059','030','Republic','politics','advanced','attic','Justice, education, and the organization of an ideal city.'),
('0003','001','History of the Peloponnesian War','history','advanced','attic','Analytical historical prose with complex syntax and argument.'),
('0016','001','Histories','history','intermediate','ionic','Herodotus investigates the conflicts between Greeks and Persians. Ionic forms differ from Attic.'),
('0548','001','Library','mythology','beginner','koine','A prose account of Greek gods, heroes, and their genealogies.'),
('0548','002','Epitome','mythology','intermediate','koine','Mythological narrative including Theseus and the Trojan cycle.'),
('0540','001','On the Murder of Eratosthenes','oratory','intermediate','attic','A courtroom defence combining narrative with persuasive argument.'),
('0540','012','Against Eratosthenes','oratory','advanced','attic','Lysias describes the Thirty’s violence and argues for accountability.'),
('0086','010','Nicomachean Ethics','philosophy','advanced','attic','Aristotle examines action, happiness, and human excellence.'),
('0086','035','Politics','politics','advanced','attic','Analysis of households, citizenship, and constitutions.'),
]
AUTHORS={'0032':'Xenophon','0059':'Plato','0003':'Thucydides','0016':'Herodotus','0548':'Apollodorus','0540':'Lysias','0086':'Aristotle'}

def main():
    checkout=Path(sys.argv[1]); revision=subprocess.check_output(['git','-C',str(checkout),'rev-parse','HEAD'],text=True).strip()
    sources=json.loads((DATA_DIR/'sources.json').read_text())
    originals=[s for s in sources['passages'] if not s.get('expanded')]
    for spec in originals:
        if spec["author"] == "Apollodorus": spec["dialect"] = "koine"
        if spec["author"] == "Thucydides": spec["level"] = "advanced"
        path = DATA_DIR/(spec["id"]+".json")
        item = json.loads(path.read_text())
        item.update(dialect=spec.get("dialect", "attic"), level=spec["level"])
        path.write_text(json.dumps(item, ensure_ascii=False, indent=2)+"\n")
    specs=list(originals)
    for author, work, title, category, level, dialect, blurb in WORKS:
        files=sorted((checkout/'data'/f'tlg{author}'/f'tlg{work}').glob('*perseus-grc*.xml'))
        path=files[0]; root=ET.parse(path).getroot(); body=root.find(f'.//{TEI}body')
        leaves=[]
        def visit(node, refs):
            ref=node.get('n')
            if node.tag==TEI+'div' and node.get('type')=='textpart' and ref: refs=refs+[ref]
            children=node.findall(TEI+'div')
            if not children and node.tag==TEI+'div' and refs and element_text(node).strip(): leaves.append(('.'.join(refs),node))
            for child in children: visit(child,refs)
        visit(body,[])
        # Consecutive opening sections, grouped near 180 words, at most 12 readings.
        groups=[]; group=[]; words=0
        for ref,node in leaves:
            group.append(ref); words+=len(element_text(node).split())
            if words>=180:
                groups.append(group); group=[]; words=0
                if len(groups)==12: break
        else:
            if group: groups.append(group)
        for index,refs in enumerate(groups):
            ref=refs[0] if len(refs)==1 else refs[0]+'–'+refs[-1]
            spec=dict(id=f'perseus-{author}-{work}-{index+1:02}',category=category,level=level,title=f'{title} · {ref}',author=AUTHORS[author],work=title,ref=ref,refs=refs,blurb=blurb,dialect=dialect,file=str(path.relative_to(checkout/'data')),urn='urn:cts:greekLit:'+path.stem,expanded=True,sequence=index+1,source_revision=revision)
            item=build_passage(spec,root)
            item.update(dialect=dialect,prerender=False,sequence=index+1)
            item['source']['url']=item['source']['url'].replace('/master/',f'/{revision}/')
            item['source']['reading_url']=f"https://scaife.perseus.org/reader/{spec['urn']}:{refs[0]}/"
            (DATA_DIR/(spec['id']+'.json')).write_text(json.dumps(item,ensure_ascii=False,indent=2)+'\n')
            specs.append(spec)
    sources['passages']=specs
    (DATA_DIR/'sources.json').write_text(json.dumps(sources,ensure_ascii=False,indent=2)+'\n')
    (DATA_DIR/'manifest.json').write_text(json.dumps([s['id'] for s in specs],indent=2)+'\n')
    print(f'{len(specs)} passages; {len(WORKS)} works; Perseus revision {revision}')
if __name__=='__main__': main()
