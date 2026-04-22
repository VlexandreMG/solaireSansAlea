## 21-04-2026
### Changement:
- On néglige la présence d'une batterie et la période de nuit (plus rien de tout ça dans nos calculs)
- On cherche toujours le pic de consommation dans la journée et la soirée 
- lors de la soirée, la puissance du panneau est toujours de -n% (comme ce qui est déjà là)
- Ajouter 3 champs : 
    - un champ pour insérer un chiffre en watt-heure,
    - un autre champ pour le prix de l'énergie selon le chiffre lors des jours férier 
    - et lors des jours ordinnaires

### Ce qu'on veut:
- d'apres le pic de consommation dans un cycle, par exemple 300 watt, on calcul combien d'argent on gagne pour un jour ordinnaire et pour les jours fériers. Par exemple j'ai une Tv de 100w de 8-11h, et un réfrigérateur de 200w de 10-12h, donc pour le pic on a 300w de 10-11h, là ça reste encore dans nos calculs actuels, ce qu'on veut maintenant c'est l'argent rapporter, pour notre exemple on va dire 1000ar pour 100wh jour ordinnaire, 2000ar jour férier, puisque notre pic de consommation est de 10-11h (1 heure), on a donc 200w de disponnible de 8-10h, 100w de disponnible de de 11-12h, et le reste de la journée 300w, du coup on obtient combien lors du jour ordinnaire et du jour férier