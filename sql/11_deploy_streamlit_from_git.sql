/* =========================================================================
   11 - Créer / mettre à jour l'app "Outil Pilotage RS" depuis Git
   -------------------------------------------------------------------------
   Prérequis : 10_git_integration.sql exécuté (GIT REPOSITORY poc_rs_repo).
   L'app lit streamlit_app.py + dashboard_template.html (multi-fichiers).
   ========================================================================= */

USE ROLE ACCOUNTADMIN;             -- ou un rôle ayant CREATE STREAMLIT sur le schéma
USE SCHEMA DLK_POC_01.APPS;

-- Création de l'app depuis le dossier du repo.
-- FROM = dossier contenant TOUS les fichiers (py + html) ; MAIN_FILE = point d'entrée.
CREATE OR REPLACE STREAMLIT outil_pilotage_rs
  FROM '@DLK_POC_01.APPS.poc_rs_repo/branches/main'
  MAIN_FILE = 'streamlit_app.py'
  QUERY_WAREHOUSE = WH_POC
  TITLE = 'Outil Pilotage RS';

-- Partage (adapter au rôle de l'équipe commerciale)
-- GRANT USAGE ON STREAMLIT outil_pilotage_rs TO ROLE <ROLE_EQUIPE>;

SHOW STREAMLITS IN SCHEMA DLK_POC_01.APPS;

/* -------------------------------------------------------------------------
   METTRE À JOUR l'app après un push GitHub (par moi ou par toi en local) :
     1) rafraîchir le clone Snowflake
     2) recharger la dernière version dans l'app
   ------------------------------------------------------------------------- */
-- ALTER GIT REPOSITORY poc_rs_repo FETCH;
-- ALTER STREAMLIT outil_pilotage_rs ADD LIVE VERSION FROM LAST;
