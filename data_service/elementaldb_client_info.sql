--
-- PostgreSQL database dump
--

-- Dumped from database version 14.12 (Ubuntu 14.12-0ubuntu0.22.04.1)
-- Dumped by pg_dump version 14.12 (Ubuntu 14.12-0ubuntu0.22.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Data for Name: clients; Type: TABLE DATA; Schema: client_info; Owner: postgres
--

INSERT INTO client_info.clients (client_id, name) VALUES ('demo', 'Demonstration');





--
-- Data for Name: site_info; Type: TABLE DATA; Schema: client_info; Owner: postgres
--

INSERT INTO client_info.site_info (site_id, name, address, location, coordinates, client_id) VALUES ('demo_london','Demo - London','Palace of Westminster, London SW1A 0AA', 'London', '(51.49966947133101, -0.12484770372778578)','demo');
INSERT INTO client_info.site_info (site_id, name, address, location, coordinates, client_id) VALUES ('bassetlaw_museum', 'Bassetlaw Museum (Amcott House)', 'Amcott House, 40 Grove St, Retford DN22 6LD', 'Retford', '(53.32227090607319,-0.9394358064784168)', 'demo');
INSERT INTO client_info.site_info (site_id, name, address, location, coordinates, client_id) VALUES ('demo_cardiff', 'Demo - Cardiff','Senedd, Pierhead St, Cardiff CF99 1SN', 'Cardiff', '(51.463479232299676, -3.1627137819539533)','demo');
INSERT INTO client_info.site_info (site_id, name, address, location, coordinates, client_id) VALUES ('demo_edinburgh', 'Demo - Edinburgh','Scottish Parliament Building, Horse Wynd, Edinburgh EH99 1SP', 'Edinburgh', '(55.95230499320703, -3.174847396715577)','demo');














--
-- PostgreSQL database dump complete
--

