-- Active: 1776393259495@@localhost@1433@solaire_db

CREATE DATABASE solaire_db;
GO

USE solaire_db;
GO

IF OBJECT_ID('utilisations', 'U') IS NOT NULL DROP TABLE utilisations;
IF OBJECT_ID('resultats', 'U') IS NOT NULL DROP TABLE resultats;
IF OBJECT_ID('tranches', 'U') IS NOT NULL DROP TABLE tranches;
IF OBJECT_ID('appareils', 'U') IS NOT NULL DROP TABLE appareils;
GO

CREATE TABLE appareils (
    id INT NOT NULL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    puissance_w FLOAT NOT NULL
);
GO

CREATE TABLE tranches (
    id INT NOT NULL PRIMARY KEY,
    label VARCHAR(10) NOT NULL,
    heure_debut INT NOT NULL,
    heure_fin INT NOT NULL
);
GO

CREATE TABLE utilisations (
    id INT NOT NULL PRIMARY KEY,
    appareil_id INT NOT NULL,
    tranche_id INT NOT NULL,
    duree_h FLOAT NOT NULL,
    heure_debut FLOAT NULL,
    heure_fin FLOAT NULL
);
GO

CREATE TABLE resultats (
    id INT NOT NULL PRIMARY KEY,
    date_calcul DATETIME NOT NULL,
    panneau_theorique_w FLOAT NOT NULL,
    panneau_achat_w FLOAT NOT NULL,
    batterie_theorique_wh FLOAT NOT NULL,
    batterie_achat_wh FLOAT NOT NULL
);
GO

CREATE TABLE type_journee (
    id INT NOT NULL PRIMARY KEY,
    nom VARCHAR(100)
);

CREATE TABLE tarif (
    id INT NOT NULL PRIMARY KEY,
    id_type_journee INT NOT NULL,
    prix FLOAT NOT NULL
);