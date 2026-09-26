/**
 * Our own grammar diagrams and maps (image records of kind "diagram" with
 * `svg: true` in the course image manifests), drawn as inline SVG in the
 * app's theme colours (CSS variables), so they match the light Reader theme
 * and scale on any screen. Released CC BY-SA 4.0 with the course.
 *
 * Each diagram is a component with no props; register it here under its
 * image id. A test checks that every `svg: true` record has a component.
 */

import type { ComponentType } from "react";
import { AlphabetChart, CaseMap, EnEisEk } from "./basics";
import { Aspect, Augment, Contract, Future, Histemi, MiddleVoice, MiVerbs, Participle, ParticipleMap, Perfect, RootAorist, Timeline, Voice } from "./verbs";
import { AgoraPlan, Kleroterion, LongWalls, PiraeusPlan, PnyxPlan, WarMap } from "./maps";
import { PlaceAdverbs, Prepositions, PothenPoi, TimeCases } from "./places";
import { Conditions, CrasisElision, GenAbs, Indirect, MenDe, Moods, Negatives, PurposeFear, ReadingStrategy, Result, Sequence, Supplementary } from "./syntax";
import { Comparison, Decl3Stem, Demonstratives, Dual, HoutosEkeinos, Numbers, Plural, Position, Relative } from "./nouns";
import { AnabasisMap, Hellespont, SicilyRetreat } from "./history";
import { Constitution, TribesMap } from "./politics";

export const DIAGRAMS: Record<string, ComponentType> = {
  "alphabet-chart": AlphabetChart,
  "diagram-case-map": CaseMap,
  "diagram-en-eis-ek": EnEisEk,
  "diagram-plural": Plural,
  "diagram-decl3-stem": Decl3Stem,
  "houtos-ekeinos": HoutosEkeinos,
  "diagram-demonstratives": Demonstratives,
  "diagram-comparison": Comparison,
  "diagram-numbers": Numbers,
  "diagram-relative": Relative,
  "diagram-position": Position,
  "diagram-dual": Dual,
  "diagram-contract": Contract,
  "diagram-middle-voice": MiddleVoice,
  "diagram-aspect": Aspect,
  "diagram-augment": Augment,
  "diagram-timeline": Timeline,
  "diagram-root-aorist": RootAorist,
  "diagram-future": Future,
  "diagram-mi-verbs": MiVerbs,
  "diagram-histemi": Histemi,
  "diagram-perfect": Perfect,
  "diagram-voice": Voice,
  "diagram-participle-map": ParticipleMap,
  "diagram-participle": Participle,
  "diagram-men-de": MenDe,
  "diagram-gen-abs": GenAbs,
  "diagram-supplementary": Supplementary,
  "diagram-moods": Moods,
  "diagram-purpose-fear": PurposeFear,
  "diagram-indirect": Indirect,
  "diagram-sequence": Sequence,
  "diagram-conditions": Conditions,
  "diagram-result": Result,
  "diagram-negatives": Negatives,
  "diagram-crasis-elision": CrasisElision,
  "diagram-reading-strategy": ReadingStrategy,
  "diagram-prepositions": Prepositions,
  "diagram-place-adverbs": PlaceAdverbs,
  "diagram-time": TimeCases,
  "diagram-pothen-poi": PothenPoi,
  "culture-agora-plan": AgoraPlan,
  "culture-long-walls": LongWalls,
  "culture-piraeus-plan": PiraeusPlan,
  "diagram-war-map": WarMap,
  "culture-pnyx-plan": PnyxPlan,
  "culture-kleroterion": Kleroterion,
  "culture-tribes-map": TribesMap,
  "culture-constitution": Constitution,
  "map-syracuse-retreat": SicilyRetreat,
  "map-aegospotami": Hellespont,
  "map-anabasis": AnabasisMap,
};
