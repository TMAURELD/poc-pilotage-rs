# Déployer le dashboard dans Snowflake (Streamlit in Snowflake)

Cette version fait tourner **ton dashboard existant à l'intérieur de Snowflake**.
Tu ouvres une URL, la donnée est live, et il n'y a **aucun identifiant à gérer** :
l'app utilise la session Snowflake de l'utilisateur connecté. Rien à installer sur
ton poste.

## Fichiers concernés (dossier POC Snowflake)

- `streamlit_app.py` — l'application (requête live + injection dans le gabarit).
- `dashboard_template.html` — ton dashboard, allégé de ses données figées (41 Ko).

## Déploiement dans Snowsight (5 minutes)

1. Connecte-toi à Snowsight (navigateur).
2. Menu de gauche : **Projects → Streamlit → + Streamlit App**.
3. Renseigne :
   - **App title** : `Outil Pilotage RS`
   - **App location** : base `DLK_POC_01` + un schéma de ton choix (ex. le schéma de staging ou un schéma dédié aux apps)
   - **Warehouse** : `WH_POC`
   Puis **Create**.
4. L'éditeur s'ouvre avec un code d'exemple. Sélectionne tout, supprime, et colle
   le contenu de **`streamlit_app.py`**.
5. Ajoute le gabarit HTML à l'app : dans l'éditeur, ouvre le panneau **Files**
   (icône fichiers à gauche de l'éditeur) → **+ / Add file from stage** ou
   **Upload**, et ajoute **`dashboard_template.html`**. Il doit se trouver au même
   niveau que `streamlit_app.py` (l'app le lit avec `open("dashboard_template.html")`).
6. Clique **Run**. L'app exécute la requête, construit les données et affiche le
   dashboard. Le bouton **🔄 Rafraîchir** vide le cache et relit Snowflake.

## Droits nécessaires

Le rôle qui exécute l'app doit avoir :
- `USAGE` sur la base `DLK_POC_01`, le schéma `"2 - Transfo (Staging)"` et le warehouse `WH_POC` ;
- `SELECT` sur la vue/table `"Transfo_BI_SortiesCaisses"`.

## Partager avec des collègues

Une fois l'app créée, elle est accessible via son URL Snowsight. Pour la partager :
bouton **Share** de l'app, puis accorde l'accès aux rôles concernés (ex. rôle
équipe commerciale). Chacun se connecte avec son propre login Snowflake — pas de
mot de passe partagé.

## Packages

Aucun package supplémentaire : `streamlit`, `snowflake-snowpark-python` et
`pandas` sont fournis d'office dans l'environnement Streamlit in Snowflake.

## Points de vigilance (POC)

- **Graphiques (Chart.js).** Le gabarit charge Chart.js depuis un CDN public. Si
  la politique réseau de Draeger bloque les CDN externes dans les composants
  Streamlit, les graphiques ne s'afficheront pas (les tableaux, si). Dans ce cas,
  on intègre Chart.js directement dans le gabarit (js embarqué) — dis-le moi et je
  te fournis la version « offline ».
- **Cases « traité » du plan d'action.** Elles sont mémorisées dans le navigateur
  (localStorage), par utilisateur et par poste — comme dans la version locale.
- **Hauteur d'affichage.** Réglée à 1500 px avec ascenseur. Ajustable dans
  `streamlit_app.py` (`components.html(..., height=1500)`).
- **Coût.** La requête est mise en cache 1 h (`ttl=3600`) : le warehouse ne tourne
  qu'au premier chargement ou après un clic sur Rafraîchir. Ajustable.

## Validation POC

Compare les indicateurs de tête (CA 2025 / CA 2026, nombre de magasins) avec la
version Excel. Référence sur le périmètre actuel : **8,55 M€ (2025)**, **8,33 M€
(2026)**, **2 740 magasins actifs**. Si les chiffres concordent, le POC est validé.
