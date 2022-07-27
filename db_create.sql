CREATE USER feeduser WITH PASSWORD 'feedpasswd';
ALTER ROLE feeduser SET client_encoding TO 'utf8';
ALTER ROLE feeduser SET default_transaction_isolation TO 'read committed';
ALTER ROLE feeduser SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE feeddb TO feeduser;


