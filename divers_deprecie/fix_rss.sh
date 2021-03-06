#!/bin/bash

refcommit=$1

curl -sL "https://raw.github.com/regardscitoyens/registre-lobbying-AN/$refcommit/data/registre-lobbying-AN-v2.csv" > /tmp/olddata.csv
curl -sL "https://raw.github.com/regardscitoyens/registre-lobbying-AN/$refcommit/rss/registre-lobbying-AN.rss" > /tmp/oldrss.rss
now=$(date -R)
dat=$(date "+%d %b %Y")
id=""
nl=$(cat /tmp/oldrss.rss | wc -l)
tail -n $(($nl - 8)) /tmp/oldrss.rss |
  head -n $(($nl - 10)) > /tmp/registremore.tmp
echo "<?xml version=\"1.0\"?>
<rss version=\"2.0\">
 <channel>
  <title>RSS Registre des représentants d'intérêts Assemblée nationale</title>
  <link>$url</link>
  <description>Les dernières modifications au registre des représentants d'intérêts de l'Assemblée nationale</description>
  <pubDate>$now</pubDate>
  <generator>RegardsCitoyens https://github.com/regardscitoyens/registre-lobbying-AN</generator>" > rss/registre-lobbying-AN.rss

diff /tmp/olddata.csv data/registre-lobbying-AN-v2.csv     | 
    grep -v "/data/registre-lobbying-AN-v2.csv" |
    grep "^[-+]"                                |
    while read line; do
      oldid=$id
      action=$(echo $line |
        sed 's/^\([+-]\).*$/\1/')
      id=$(echo $line |
        sed 's/^[+-]\([0-9]\+\),.*$/\1/')
      nom=$(echo $line |
        sed 's/^[+-][0-9]\+,"\(\([^"]\+\(""\)\?\)\+\)",.*$/\1/' |
        sed 's/""/"/g' |
        sed 's/\&/\&nbsp;/g')
      safenom=$(echo $nom |
        sed 's/\&nbsp;/\\\&/g' |
        sed 's/"/""/g')
      orgtype=$(echo $line |                                              
        sed 's/^[+-][0-9]\+,"'"$safenom"'",[^,]*,"\([^"]\+\)",.*$/\1/')
      case "$action" in
        "+")
            desc="Nouvel inscrit a"
            statut="nouveau";;
        "-")
            desc="Retrait d"
            statut="retiré";;
      esac
      if [ "$id" != "$oldid" ] && [ -f "/tmp/registreitem.tmp" ] ; then
        cat /tmp/registreitem.tmp >> rss/registre-lobbying-AN.rss
      elif [ "$id" == "$oldid" ] && [ "$action" == "+" ]; then
        desc="Modifications des informations d"
        statut="modifié"
      fi
      echo "  <item>
   <title>$nom ($orgtype, $statut)</title>
   <link>${rooturl}detail/$id</link>
   <description><![CDATA[${desc}u registre le $dat : $nom ($orgtype)]]></description>
   <pubDate>$now</pubDate>
  </item>" > /tmp/registreitem.tmp
    done
  cat /tmp/registreitem.tmp >> rss/registre-lobbying-AN.rss
  rm -f /tmp/registreitem.tmp
  if test -s /tmp/registremore.tmp; then
    cat /tmp/registremore.tmp >> rss/registre-lobbying-AN.rss
  fi
  rm -f /tmp/registremore.tmp
  echo " </channel>
</rss>" >> rss/registre-lobbying-AN.rss


