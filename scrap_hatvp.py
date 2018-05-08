#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, re, json, time
import requests

DEBUG = len(sys.argv) > 1

imgpath = os.path.join("images", "logos-HATVP")
for d in ["data", "images", imgpath]:
    if not os.path.exists(d):
        os.makedirs(d)

imgfmt = lambda f: "png" if "png" in f else "jpg"

data = []
done = {}
actions = {}

re_format_date = re.compile(ur"(..)[-/](..)[-/](....)[ à]*(..:..:..)?$")
_reformat_date = lambda x: "%s-%s-%s" % (x.group(3), x.group(2), x.group(1)) + ("T" + x.group(4) if x.group(4) else "")
def reformat_date(obj):
    for field in [
      "dateCreation",
      "dateDebut",
      "dateFin",
      "publicationDate",
      "datePremierePublication"
    ]:
        if field in obj:
            obj[field] = re_format_date.sub(_reformat_date, obj[field])

def safe_dl(url, fail=False, retry=5):
    try:
        return requests.get(url).json()
    except Exception as e:
        if retry:
            time.sleep(1)
            return safe_dl(url, fail=fail, retry=retry-1)
        print "ERROR reading %s. %s: %s" % (url, type(e), e)
        if fail:
            exit(1)
        return None

hatvp = safe_dl("https://www.hatvp.fr/agora/stock.json", True)

for act in hatvp[2]:
    key = "num_organisation"
    if key not in act:
        key = "nom_organisation"
    if act[key] not in actions:
        actions[act[key]] = []
    reformat_date(act)
    actions[act[key]].append(act)

for org in hatvp[0] + hatvp[1]:
    if org["identifiantNational"] in done:
        continue
    done[org["identifiantNational"]] = True
    org["url_json"] = "https://www.hatvp.fr/agora/%s.json" % org["identifiantNational"]
    reformat_date(org)
    details = safe_dl(org["url_json"])
    if details:
        reformat_date(details["publicationCourante"])
        org.update(details["publicationCourante"])

        [reformat_date(h) for h in details["historique"]]
        historique = [h for h in details["historique"] if h["dateCreation"] != org["dateCreation"]]
        org["historique"] = sorted(historique, key=lambda x: x["dateCreation"])

        exercices = [e["publicationCourante"] for e in details.get("exercices", [])]
        [reformat_date(e) for e in exercices]
        [reformat_date(a["publicationCourante"]) for e in exercices for a in e.get("activites", [])]
        [reformat_date(h) for e in exercices for a in e.get("activites", []) for h in a.get("historique", [])]
        org["exercices"] = sorted(exercices, key=lambda x: x["dateDebut"])

        histo_exercices = [h for e in details.get("exercices", []) for h in e.get("historique", [])]
        [reformat_date(h) for h in histo_exercices]
        org["historique_exercices"] = sorted(histo_exercices, key=lambda x: x["dateCreation"])

        orgactions = actions.get(org["identifiantNational"], []) + actions.get(org["denomination"], [])
        org["resumes_actions"] = sorted(orgactions, key=lambda x: x["publicationDate"] + x["objet"])

        if DEBUG:
            ne = sum([len(e.get("activites", [])) for e in org["exercices"]])
            na = len(org["resumes_actions"])
            if na != ne:
                print "_________________________________________________________________________"
                print "WARNING diff activites:", na, ne, org["identifiantNational"]
                print

        if "logo" in details:
            imgfile = "%s.%s" % (org["identifiantNational"], imgfmt(details["logoType"]))
            with open(os.path.join(imgpath, imgfile), "wb") as f:
                f.write(details["logo"].decode('base64'))

    data.append(org)

data = sorted(data, key=lambda x: x["denomination"])

with open(os.path.join("data", "registre-lobbying-HATVP.json"), "w") as f:
    print >> f, json.dumps(data, f, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8")
