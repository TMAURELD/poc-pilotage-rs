/* =========================================================================
   10 - Connecter Snowflake au dépôt GitHub (à exécuter UNE fois)
   -------------------------------------------------------------------------
   Rôle requis : ACCOUNTADMIN (ou rôle avec CREATE INTEGRATION + CREATE SECRET).
   Remplace les <...> avant d'exécuter.
   ========================================================================= */

USE ROLE ACCOUNTADMIN;

-- Où stocker les objets Git (secret, integration, repo).
-- On reste dans la base du POC ; adapte le schéma si besoin.
USE DATABASE DLK_POC_01;
CREATE SCHEMA IF NOT EXISTS APPS;
USE SCHEMA DLK_POC_01.APPS;

-- 1) Secret : Personal Access Token GitHub (droits lecture + écriture sur le repo)
CREATE OR REPLACE SECRET github_secret
  TYPE     = password
  USERNAME = 'TMAURELD'
  PASSWORD = '<UN_NOUVEAU_PAT_POUR_SNOWFLAKE>';  -- recrée un PAT dédié (Contents R/W)

-- 2) API integration autorisant l'accès à ton espace GitHub
CREATE OR REPLACE API INTEGRATION github_api_integration
  API_PROVIDER = git_https_api
  API_ALLOWED_PREFIXES = ('https://github.com/TMAURELD')
  ALLOWED_AUTHENTICATION_SECRETS = (github_secret)
  ENABLED = TRUE;

-- 3) Clone du dépôt dans Snowflake
CREATE OR REPLACE GIT REPOSITORY poc_rs_repo
  API_INTEGRATION = github_api_integration
  GIT_CREDENTIALS = github_secret
  ORIGIN = 'https://github.com/TMAURELD/poc-pilotage-rd.git';

-- 4) Récupérer le contenu et vérifier
ALTER GIT REPOSITORY poc_rs_repo FETCH;
SHOW GIT BRANCHES IN poc_rs_repo;
L