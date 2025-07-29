-- init.sql
CREATE DATABASE messagedb;

\connect messagedb

CREATE TABLE message (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL
);