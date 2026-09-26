"""Gold tables for the verb conjugation engine (Classical Attic)."""

from __future__ import annotations

import pytest

from app.greek.morph.verb import conjugate_entry
from app.vocab import load_entries


@pytest.fixture(scope="module")
def lex():
    return {e["lemma"]: e for e in load_entries()}


def cells(lex, lemma, tense, voice, mood):
    t = conjugate_entry(lex[lemma])
    assert t is not None, lemma
    for system in t["systems"]:
        for tb in system["tables"]:
            if (tb["tense"], tb["voice"], tb["mood"]) == (tense, voice, mood):
                return ["/".join(c["forms"]) for c in tb["cells"]]
    raise AssertionError(f"{lemma}: no table {tense} {voice} {mood}")


GOLD = [
    # λύω — the model verb, every system
    ("λύω", "present", "active", "indicative", "λύω λύεις λύει λύομεν λύετε λύουσι(ν)"),
    ("λύω", "present", "active", "subjunctive", "λύω λύῃς λύῃ λύωμεν λύητε λύωσι(ν)"),
    ("λύω", "present", "active", "optative", "λύοιμι λύοις λύοι λύοιμεν λύοιτε λύοιεν"),
    ("λύω", "present", "active", "imperative", "λῦε λυέτω λύετε λυόντων"),
    ("λύω", "present", "active", "infinitive", "λύειν"),
    ("λύω", "present", "active", "participle", "λύων λύουσα λῦον λύοντος"),
    ("λύω", "imperfect", "active", "indicative", "ἔλυον ἔλυες ἔλυε(ν) ἐλύομεν ἐλύετε ἔλυον"),
    ("λύω", "present", "middle/passive", "indicative", "λύομαι λύῃ/λύει λύεται λυόμεθα λύεσθε λύονται"),
    ("λύω", "present", "middle/passive", "optative", "λυοίμην λύοιο λύοιτο λυοίμεθα λύοισθε λύοιντο"),
    ("λύω", "present", "middle/passive", "imperative", "λύου λυέσθω λύεσθε λυέσθων"),
    ("λύω", "imperfect", "middle/passive", "indicative", "ἐλυόμην ἐλύου ἐλύετο ἐλυόμεθα ἐλύεσθε ἐλύοντο"),
    ("λύω", "future", "active", "indicative", "λύσω λύσεις λύσει λύσομεν λύσετε λύσουσι(ν)"),
    ("λύω", "future", "passive", "indicative", "λυθήσομαι λυθήσῃ/λυθήσει λυθήσεται λυθησόμεθα λυθήσεσθε λυθήσονται"),
    ("λύω", "aorist", "active", "indicative", "ἔλυσα ἔλυσας ἔλυσε(ν) ἐλύσαμεν ἐλύσατε ἔλυσαν"),
    ("λύω", "aorist", "active", "subjunctive", "λύσω λύσῃς λύσῃ λύσωμεν λύσητε λύσωσι(ν)"),
    ("λύω", "aorist", "active", "optative", "λύσαιμι λύσαις/λύσειας λύσαι/λύσειε(ν) λύσαιμεν λύσαιτε λύσαιεν/λύσειαν"),
    ("λύω", "aorist", "active", "imperative", "λῦσον λυσάτω λύσατε λυσάντων"),
    ("λύω", "aorist", "active", "infinitive", "λῦσαι"),
    ("λύω", "aorist", "active", "participle", "λύσας λύσασα λῦσαν λύσαντος"),
    ("λύω", "aorist", "middle", "indicative", "ἐλυσάμην ἐλύσω ἐλύσατο ἐλυσάμεθα ἐλύσασθε ἐλύσαντο"),
    ("λύω", "aorist", "middle", "imperative", "λῦσαι λυσάσθω λύσασθε λυσάσθων"),
    ("λύω", "aorist", "middle", "infinitive", "λύσασθαι"),
    ("λύω", "aorist", "passive", "indicative", "ἐλύθην ἐλύθης ἐλύθη ἐλύθημεν ἐλύθητε ἐλύθησαν"),
    ("λύω", "aorist", "passive", "subjunctive", "λυθῶ λυθῇς λυθῇ λυθῶμεν λυθῆτε λυθῶσι(ν)"),
    ("λύω", "aorist", "passive", "optative", "λυθείην λυθείης λυθείη λυθεῖμεν/λυθείημεν λυθεῖτε/λυθείητε λυθεῖεν/λυθείησαν"),
    ("λύω", "aorist", "passive", "imperative", "λύθητι λυθήτω λύθητε λυθέντων"),
    ("λύω", "aorist", "passive", "infinitive", "λυθῆναι"),
    ("λύω", "aorist", "passive", "participle", "λυθείς λυθεῖσα λυθέν λυθέντος"),
    ("λύω", "perfect", "active", "indicative", "λέλυκα λέλυκας λέλυκε(ν) λελύκαμεν λελύκατε λελύκασι(ν)"),
    ("λύω", "perfect", "active", "infinitive", "λελυκέναι"),
    ("λύω", "perfect", "active", "participle", "λελυκώς λελυκυῖα λελυκός λελυκότος"),
    ("λύω", "pluperfect", "active", "indicative", "ἐλελύκη ἐλελύκης ἐλελύκει(ν) ἐλελύκεμεν ἐλελύκετε ἐλελύκεσαν"),
    ("λύω", "perfect", "middle/passive", "indicative", "λέλυμαι λέλυσαι λέλυται λελύμεθα λέλυσθε λέλυνται"),
    ("λύω", "perfect", "middle/passive", "infinitive", "λελύσθαι"),
    ("λύω", "perfect", "middle/passive", "participle", "λελυμένος λελυμένη λελυμένον λελυμένου"),
    ("λύω", "pluperfect", "middle/passive", "indicative", "ἐλελύμην ἐλέλυσο ἐλέλυτο ἐλελύμεθα ἐλέλυσθε ἐλέλυντο"),
    ("λύω", "future perfect", "middle/passive", "indicative", "λελύσομαι λελύσῃ/λελύσει λελύσεται λελυσόμεθα λελύσεσθε λελύσονται"),
    # contract verbs
    ("τιμάω", "present", "active", "indicative", "τιμῶ τιμᾷς τιμᾷ τιμῶμεν τιμᾶτε τιμῶσι(ν)"),
    ("τιμάω", "present", "active", "subjunctive", "τιμῶ τιμᾷς τιμᾷ τιμῶμεν τιμᾶτε τιμῶσι(ν)"),
    ("τιμάω", "present", "active", "optative", "τιμῴην τιμῴης τιμῴη τιμῷμεν/τιμῴημεν τιμῷτε/τιμῴητε τιμῷεν/τιμῴησαν"),
    ("τιμάω", "present", "active", "imperative", "τίμα τιμάτω τιμᾶτε τιμώντων"),
    ("τιμάω", "present", "active", "infinitive", "τιμᾶν"),
    ("τιμάω", "present", "active", "participle", "τιμῶν τιμῶσα τιμῶν τιμῶντος"),
    ("τιμάω", "imperfect", "active", "indicative", "ἐτίμων ἐτίμας ἐτίμα ἐτιμῶμεν ἐτιμᾶτε ἐτίμων"),
    ("τιμάω", "present", "middle/passive", "indicative", "τιμῶμαι τιμᾷ τιμᾶται τιμώμεθα τιμᾶσθε τιμῶνται"),
    ("τιμάω", "imperfect", "middle/passive", "indicative", "ἐτιμώμην ἐτιμῶ ἐτιμᾶτο ἐτιμώμεθα ἐτιμᾶσθε ἐτιμῶντο"),
    ("ποιέω", "present", "active", "indicative", "ποιῶ ποιεῖς ποιεῖ ποιοῦμεν ποιεῖτε ποιοῦσι(ν)"),
    ("ποιέω", "present", "active", "imperative", "ποίει ποιείτω ποιεῖτε ποιούντων"),
    ("ποιέω", "present", "active", "participle", "ποιῶν ποιοῦσα ποιοῦν ποιοῦντος"),
    ("ποιέω", "imperfect", "active", "indicative", "ἐποίουν ἐποίεις ἐποίει ἐποιοῦμεν ἐποιεῖτε ἐποίουν"),
    ("ποιέω", "present", "middle/passive", "indicative", "ποιοῦμαι ποιῇ/ποιεῖ ποιεῖται ποιούμεθα ποιεῖσθε ποιοῦνται"),
    ("ποιέω", "present", "middle/passive", "infinitive", "ποιεῖσθαι"),
    ("δηλόω", "present", "active", "indicative", "δηλῶ δηλοῖς δηλοῖ δηλοῦμεν δηλοῦτε δηλοῦσι(ν)"),
    ("δηλόω", "present", "active", "subjunctive", "δηλῶ δηλοῖς δηλοῖ δηλῶμεν δηλῶτε δηλῶσι(ν)".replace("δηλοῖς δηλοῖ", "δηλῷς δηλῷ")),
    ("δηλόω", "present", "active", "imperative", "δήλου δηλούτω δηλοῦτε δηλούντων"),
    ("δηλόω", "imperfect", "active", "indicative", "ἐδήλουν ἐδήλους ἐδήλου ἐδηλοῦμεν ἐδηλοῦτε ἐδήλουν"),
    ("ζάω", "present", "active", "indicative", "ζῶ ζῇς ζῇ ζῶμεν ζῆτε ζῶσι(ν)"),
    ("ζάω", "present", "active", "infinitive", "ζῆν"),
    ("πλέω", "present", "active", "indicative", "πλέω πλεῖς πλεῖ πλέομεν πλεῖτε πλέουσι(ν)"),
    # -μι verbs
    ("δίδωμι", "present", "active", "indicative", "δίδωμι δίδως δίδωσι(ν) δίδομεν δίδοτε διδόασι(ν)"),
    ("δίδωμι", "present", "active", "subjunctive", "διδῶ διδῷς διδῷ διδῶμεν διδῶτε διδῶσι(ν)"),
    ("δίδωμι", "present", "active", "optative", "διδοίην διδοίης διδοίη διδοῖμεν διδοῖτε διδοῖεν"),
    ("δίδωμι", "present", "active", "imperative", "δίδου διδότω δίδοτε διδόντων"),
    ("δίδωμι", "present", "active", "infinitive", "διδόναι"),
    ("δίδωμι", "present", "active", "participle", "διδούς διδοῦσα διδόν διδόντος"),
    ("δίδωμι", "imperfect", "active", "indicative", "ἐδίδουν ἐδίδους ἐδίδου ἐδίδομεν ἐδίδοτε ἐδίδοσαν"),
    ("δίδωμι", "aorist", "active", "indicative", "ἔδωκα ἔδωκας ἔδωκε(ν) ἔδομεν ἔδοτε ἔδοσαν"),
    ("δίδωμι", "aorist", "active", "subjunctive", "δῶ δῷς δῷ δῶμεν δῶτε δῶσι(ν)"),
    ("δίδωμι", "aorist", "active", "optative", "δοίην δοίης δοίη δοῖμεν δοῖτε δοῖεν"),
    ("δίδωμι", "aorist", "active", "imperative", "δός δότω δότε δόντων"),
    ("δίδωμι", "aorist", "active", "infinitive", "δοῦναι"),
    ("δίδωμι", "aorist", "active", "participle", "δούς δοῦσα δόν δόντος"),
    ("δίδωμι", "aorist", "middle", "indicative", "ἐδόμην ἔδου ἔδοτο ἐδόμεθα ἔδοσθε ἔδοντο"),
    ("δίδωμι", "aorist", "middle", "imperative", "δοῦ δόσθω δόσθε δόσθων"),
    ("τίθημι", "present", "active", "indicative", "τίθημι τίθης τίθησι(ν) τίθεμεν τίθετε τιθέασι(ν)"),
    ("τίθημι", "imperfect", "active", "indicative", "ἐτίθην ἐτίθεις ἐτίθει ἐτίθεμεν ἐτίθετε ἐτίθεσαν"),
    ("τίθημι", "aorist", "active", "indicative", "ἔθηκα ἔθηκας ἔθηκε(ν) ἔθεμεν ἔθετε ἔθεσαν"),
    ("τίθημι", "aorist", "active", "infinitive", "θεῖναι"),
    ("τίθημι", "aorist", "active", "participle", "θείς θεῖσα θέν θέντος"),
    ("τίθημι", "aorist", "middle", "indicative", "ἐθέμην ἔθου ἔθετο ἐθέμεθα ἔθεσθε ἔθεντο"),
    ("ἵστημι", "present", "active", "indicative", "ἵστημι ἵστης ἵστησι(ν) ἵσταμεν ἵστατε ἱστᾶσι(ν)"),
    ("ἵστημι", "present", "active", "subjunctive", "ἱστῶ ἱστῇς ἱστῇ ἱστῶμεν ἱστῆτε ἱστῶσι(ν)"),
    ("ἵστημι", "present", "active", "infinitive", "ἱστάναι"),
    ("ἵστημι", "imperfect", "active", "indicative", "ἵστην ἵστης ἵστη ἵσταμεν ἵστατε ἵστασαν"),
    ("ἵστημι", "aorist", "active", "indicative", "ἔστησα ἔστησας ἔστησε(ν) ἐστήσαμεν ἐστήσατε ἔστησαν"),
    ("ἵστημι", "root aorist", "active", "indicative", "ἔστην ἔστης ἔστη ἔστημεν ἔστητε ἔστησαν"),
    ("ἵστημι", "root aorist", "active", "subjunctive", "στῶ στῇς στῇ στῶμεν στῆτε στῶσι(ν)"),
    ("ἵστημι", "root aorist", "active", "optative", "σταίην σταίης σταίη σταῖμεν σταῖτε σταῖεν"),
    ("ἵστημι", "root aorist", "active", "imperative", "στῆθι στήτω στῆτε στάντων"),
    ("ἵστημι", "root aorist", "active", "infinitive", "στῆναι"),
    ("ἵστημι", "root aorist", "active", "participle", "στάς στᾶσα στάν στάντος"),
    ("ἵστημι", "pluperfect", "active", "indicative", "εἱστήκη εἱστήκης εἱστήκει(ν) ἕσταμεν/εἱστήκεμεν ἕστατε/εἱστήκετε ἕστασαν/εἱστήκεσαν"),
    # short perfect of ἵστημι (Smyth § 417)
    ("ἵστημι", "perfect", "active", "indicative", "ἕστηκα ἕστηκας ἕστηκε(ν) ἕσταμεν/ἑστήκαμεν ἕστατε/ἑστήκατε ἑστᾶσι(ν)/ἑστήκασι(ν)"),
    ("ἵστημι", "perfect", "active", "infinitive", "ἑστάναι/ἑστηκέναι"),
    ("ἵστημι", "perfect", "active", "participle", "ἑστηκώς/ἑστώς ἑστηκυῖα/ἑστῶσα ἑστηκός/ἑστός ἑστηκότος/ἑστῶτος"),
    ("δείκνυμι", "present", "active", "indicative", "δείκνυμι δείκνυς δείκνυσι(ν) δείκνυμεν δείκνυτε δεικνύασι(ν)"),
    ("δείκνυμι", "present", "active", "infinitive", "δεικνύναι"),
    ("δείκνυμι", "imperfect", "active", "indicative", "ἐδείκνυν ἐδείκνυς ἐδείκνυ ἐδείκνυμεν ἐδείκνυτε ἐδείκνυσαν"),
    ("δύναμαι", "present", "middle", "indicative", "δύναμαι δύνασαι δύναται δυνάμεθα δύνασθε δύνανται"),
    ("δύναμαι", "present", "middle", "subjunctive", "δύνωμαι δύνῃ δύνηται δυνώμεθα δύνησθε δύνωνται"),
    ("δύναμαι", "imperfect", "middle", "indicative", "ἐδυνάμην ἐδύνασο ἐδύνατο ἐδυνάμεθα ἐδύνασθε ἐδύναντο"),
    # irregular hand tables
    ("εἰμί", "present", "active", "indicative", "εἰμί εἶ ἐστί(ν) ἐσμέν ἐστέ εἰσί(ν)"),
    ("εἰμί", "imperfect", "active", "indicative", "ἦ/ἦν ἦσθα ἦν ἦμεν ἦτε ἦσαν"),
    ("εἰμί", "present", "active", "participle", "ὤν οὖσα ὄν ὄντος"),
    ("εἶμι", "present", "active", "indicative", "εἶμι εἶ εἶσι(ν) ἴμεν ἴτε ἴασι(ν)"),
    ("φημί", "present", "active", "indicative", "φημί φῄς φησί(ν) φαμέν φατέ φασί(ν)"),
    ("οἶδα", "perfect", "active", "indicative", "οἶδα οἶσθα οἶδε(ν) ἴσμεν ἴστε ἴσασι(ν)"),
    ("ἀφίημι", "aorist", "active", "indicative", "ἀφῆκα ἀφῆκας ἀφῆκε(ν) ἀφεῖμεν ἀφεῖτε ἀφεῖσαν"),
    # second aorists, root aorists, liquids, passives, deponents, compounds
    ("λαμβάνω", "aorist", "active", "indicative", "ἔλαβον ἔλαβες ἔλαβε(ν) ἐλάβομεν ἐλάβετε ἔλαβον"),
    ("λαμβάνω", "aorist", "active", "imperative", "λαβέ λαβέτω λάβετε λαβόντων"),
    ("λαμβάνω", "aorist", "active", "infinitive", "λαβεῖν"),
    ("λαμβάνω", "aorist", "active", "participle", "λαβών λαβοῦσα λαβόν λαβόντος"),
    ("λαμβάνω", "aorist", "middle", "imperative", "λαβοῦ λαβέσθω λάβεσθε λαβέσθων"),
    ("λαμβάνω", "perfect", "middle/passive", "indicative", "εἴλημμαι εἴληψαι εἴληπται εἰλήμμεθα εἴληφθε εἰλημμένοι_εἰσί(ν)"),
    ("φαίνω", "future", "active", "indicative", "φανῶ φανεῖς φανεῖ φανοῦμεν φανεῖτε φανοῦσι(ν)"),
    ("φαίνω", "aorist", "active", "indicative", "ἔφηνα ἔφηνας ἔφηνε(ν) ἐφήναμεν ἐφήνατε ἔφηναν"),
    ("φαίνω", "aorist", "active", "infinitive", "φῆναι"),
    ("φαίνω", "second aorist", "passive", "indicative", "ἐφάνην ἐφάνης ἐφάνη ἐφάνημεν ἐφάνητε ἐφάνησαν"),
    ("φαίνω", "second aorist", "passive", "imperative", "φάνηθι φανήτω φάνητε φανέντων"),
    ("φαίνω", "perfect", "middle/passive", "indicative", "πέφασμαι πέφανσαι πέφανται πεφάσμεθα πέφανθε πεφασμένοι_εἰσί(ν)"),
    ("γράφω", "second aorist", "passive", "infinitive", "γραφῆναι"),
    ("γράφω", "perfect", "middle/passive", "indicative", "γέγραμμαι γέγραψαι γέγραπται γεγράμμεθα γέγραφθε γεγραμμένοι_εἰσί(ν)"),
    ("βαίνω", "aorist", "active", "indicative", "ἔβην ἔβης ἔβη ἔβημεν ἔβητε ἔβησαν"),
    ("βαίνω", "aorist", "active", "participle", "βάς βᾶσα βάν βάντος"),
    ("γιγνώσκω", "aorist", "active", "indicative", "ἔγνων ἔγνως ἔγνω ἔγνωμεν ἔγνωτε ἔγνωσαν"),
    ("γιγνώσκω", "aorist", "active", "imperative", "γνῶθι γνώτω γνῶτε γνόντων"),
    ("γιγνώσκω", "aorist", "active", "infinitive", "γνῶναι"),
    ("ἀποθνῄσκω", "imperfect", "active", "indicative", "ἀπέθνῃσκον ἀπέθνῃσκες ἀπέθνῃσκε(ν) ἀπεθνῄσκομεν ἀπεθνῄσκετε ἀπέθνῃσκον"),
    ("ἀποθνῄσκω", "aorist", "active", "indicative", "ἀπέθανον ἀπέθανες ἀπέθανε(ν) ἀπεθάνομεν ἀπεθάνετε ἀπέθανον"),
    ("ἀποθνῄσκω", "aorist", "active", "infinitive", "ἀποθανεῖν"),
    ("ἀποθνῄσκω", "future", "middle", "indicative", "ἀποθανοῦμαι ἀποθανῇ/ἀποθανεῖ ἀποθανεῖται ἀποθανούμεθα ἀποθανεῖσθε ἀποθανοῦνται"),
    ("γίγνομαι", "aorist", "middle", "indicative", "ἐγενόμην ἐγένου ἐγένετο ἐγενόμεθα ἐγένεσθε ἐγένοντο"),
    ("γίγνομαι", "aorist", "middle", "infinitive", "γενέσθαι"),
    ("γίγνομαι", "perfect", "active", "indicative", "γέγονα γέγονας γέγονε(ν) γεγόναμεν γεγόνατε γεγόνασι(ν)"),
    ("βούλομαι", "aorist", "passive", "indicative", "ἐβουλήθην ἐβουλήθης ἐβουλήθη ἐβουλήθημεν ἐβουλήθητε ἐβουλήθησαν"),
    ("ἔρχομαι", "aorist", "active", "indicative", "ἦλθον ἦλθες ἦλθε(ν) ἤλθομεν ἤλθετε ἦλθον"),
    ("ἔρχομαι", "aorist", "active", "imperative", "ἐλθέ ἐλθέτω ἔλθετε ἐλθόντων"),
    ("ἔχω", "imperfect", "active", "indicative", "εἶχον εἶχες εἶχε(ν) εἴχομεν εἴχετε εἶχον"),
    ("ἔχω", "aorist", "active", "infinitive", "σχεῖν"),
    ("ὁράω", "imperfect", "active", "indicative", "ἑώρων ἑώρας ἑώρα ἑωρῶμεν ἑωρᾶτε ἑώρων"),
    ("ὁράω", "aorist", "active", "imperative", "ἰδέ ἰδέτω ἴδετε ἰδόντων"),
    ("ὁράω", "aorist", "passive", "infinitive", "ὀφθῆναι"),
    ("λέγω", "aorist", "active", "imperative", "εἰπέ εἰπέτω εἴπετε εἰπόντων"),
    ("λέγω", "aorist", "active", "participle", "εἰπών εἰποῦσα εἰπόν εἰπόντος"),
    ("φέρω", "aorist", "active", "infinitive", "ἐνέγκαι"),
    ("φέρω", "second aorist", "active", "infinitive", "ἐνεγκεῖν"),
    ("παρέχω", "imperfect", "active", "indicative", "παρεῖχον παρεῖχες παρεῖχε(ν) παρείχομεν παρείχετε παρεῖχον"),
    ("παρέχω", "aorist", "active", "infinitive", "παρασχεῖν"),
    ("καθίστημι", "imperfect", "active", "indicative", "καθίστην καθίστης καθίστη καθίσταμεν καθίστατε καθίστασαν"),
    ("καθίστημι", "root aorist", "active", "infinitive", "καταστῆναι"),
    ("ἀφαιρέω", "aorist", "active", "infinitive", "ἀφελεῖν"),
    ("εὑρίσκω", "aorist", "active", "indicative", "ηὗρον/εὗρον ηὗρες/εὗρες ηὗρε(ν)/εὗρε(ν) ηὕρομεν/εὕρομεν ηὕρετε/εὕρετε ηὗρον/εὗρον"),
    ("ἀκούω", "perfect", "active", "indicative", "ἀκήκοα ἀκήκοας ἀκήκοε(ν) ἀκηκόαμεν ἀκηκόατε ἀκηκόασι(ν)"),
    ("νομίζω", "future", "active", "indicative", "νομιῶ νομιεῖς νομιεῖ νομιοῦμεν νομιεῖτε νομιοῦσι(ν)"),
    ("νομίζω", "aorist", "active", "participle", "νομίσας νομίσασα νομίσαν νομίσαντος"),
    ("δεῖ", "present", "active", "indicative", "δεῖ"),
    ("χρή", "imperfect", "active", "indicative", "χρῆν/ἐχρῆν"),
    # proofread 2026-09-14: compounds, augments, long stem vowels, aliases
    ("αἴρω", "aorist", "active", "infinitive", "ἆραι"),
    ("αἴρω", "aorist", "active", "imperative", "ἆρον ἀράτω ἄρατε ἀράντων"),
    ("αἴρω", "aorist", "active", "participle", "ἄρας ἄρασα ἆραν ἄραντος"),
    ("κρίνω", "aorist", "active", "infinitive", "κρῖναι"),
    ("κρίνω", "aorist", "active", "imperative", "κρῖνον κρινάτω κρίνατε κρινάντων"),
    ("ἀφικνέομαι", "perfect", "middle/passive", "indicative", "ἀφῖγμαι ἀφῖξαι ἀφῖκται ἀφίγμεθα ἀφῖχθε ἀφιγμένοι_εἰσί(ν)"),
    ("ἀφικνέομαι", "pluperfect", "middle/passive", "indicative", "ἀφίγμην ἀφῖξο ἀφῖκτο ἀφίγμεθα ἀφῖχθε ἀφιγμένοι_ἦσαν"),
    ("εἶδον", "aorist", "active", "indicative", "εἶδον εἶδες εἶδε(ν) εἴδομεν εἴδετε εἶδον"),
    ("εἶδον", "aorist", "active", "participle", "ἰδών ἰδοῦσα ἰδόν ἰδόντος"),
    ("ἀπόλλυμι", "pluperfect", "active", "indicative", "ἀπωλωλέκη ἀπωλωλέκης ἀπωλωλέκει(ν) ἀπωλωλέκεμεν ἀπωλωλέκετε ἀπωλωλέκεσαν"),
    ("ἐάω", "imperfect", "active", "indicative", "εἴων εἴας εἴα εἰῶμεν εἰᾶτε εἴων"),
    ("ἐργάζομαι", "imperfect", "middle", "indicative", "εἰργαζόμην εἰργάζου εἰργάζετο εἰργαζόμεθα εἰργάζεσθε εἰργάζοντο"),
    ("ἕπομαι", "imperfect", "middle", "indicative", "εἱπόμην εἵπου εἵπετο εἱπόμεθα εἵπεσθε εἵποντο"),
    ("συμβαίνω", "pluperfect", "active", "indicative", "συνεβεβήκη συνεβεβήκης συνεβεβήκει(ν) συνεβεβήκεμεν συνεβεβήκετε συνεβεβήκεσαν"),
    ("ὑπάρχω", "perfect", "middle/passive", "indicative", "ὑπῆργμαι ὑπῆρξαι ὑπῆρκται ὑπήργμεθα ὑπῆρχθε ὑπηργμένοι_εἰσί(ν)"),
    ("ἔχω", "aorist", "active", "imperative", "σχές σχέτω σχέτε σχόντων"),
    ("παρέχω", "aorist", "active", "imperative", "παράσχες παρασχέτω παράσχετε παρασχόντων"),
    ("ἀναιρέω", "imperfect", "active", "indicative", "ἀνῄρουν ἀνῄρεις ἀνῄρει ἀνῃροῦμεν ἀνῃρεῖτε ἀνῄρουν"),
    ("κατηγορέω", "pluperfect", "active", "indicative", "κατηγορήκη κατηγορήκης κατηγορήκει(ν) κατηγορήκεμεν κατηγορήκετε κατηγορήκεσαν"),
    ("ὁράω", "pluperfect", "active", "indicative", "ἑωράκη ἑωράκης ἑωράκει(ν) ἑωράκεμεν ἑωράκετε ἑωράκεσαν"),
    ("ἐλαύνω", "perfect", "active", "indicative", "ἐλήλακα ἐλήλακας ἐλήλακε(ν) ἐληλάκαμεν ἐληλάκατε ἐληλάκασι(ν)"),
]


@pytest.mark.parametrize("lemma,tense,voice,mood,expected", GOLD, ids=[f"{g[0]}-{g[1]}-{g[2]}-{g[3]}" for g in GOLD])
def test_verb_paradigms(lex, lemma, tense, voice, mood, expected):
    assert cells(lex, lemma, tense, voice, mood) == [x.replace("_", " ") for x in expected.split()]


def test_every_verb_conjugates(lex):
    for e in lex.values():
        if e["kind"] == "verb" and not e["morph"].get("alias_of"):
            t = conjugate_entry(e)
            assert t and t["systems"], e["lemma"]
            for system in t["systems"]:
                for tb in system["tables"]:
                    for c in tb["cells"]:
                        for f in c["forms"]:
                            assert f and "ἐἐ" not in f and "̔̔" not in f, (e["lemma"], tb, f)
