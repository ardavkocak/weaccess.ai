--
-- PostgreSQL database dump
--

\restrict qKTkG6mLcc8PEE83435dzUpaiXdfT6kAfDpxczuMSNDTK4iSPGXK8yEfq1hEN8C

-- Dumped from database version 16.14 (Homebrew)
-- Dumped by pg_dump version 16.14 (Homebrew)

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

ALTER TABLE IF EXISTS ONLY public.inventory_notification DROP CONSTRAINT IF EXISTS inventory_notification_user_id_b5616c82_fk_accounts_user_id;
ALTER TABLE IF EXISTS ONLY public.inventory_employee DROP CONSTRAINT IF EXISTS inventory_employee_user_id_df4f6208_fk_accounts_user_id;
ALTER TABLE IF EXISTS ONLY public.inventory_employee DROP CONSTRAINT IF EXISTS inventory_employee_company_id_8bec41c0_fk_inventory_company_id;
ALTER TABLE IF EXISTS ONLY public.inventory_assignment DROP CONSTRAINT IF EXISTS inventory_assignment_returned_by_id_9ef8825a_fk_accounts_;
ALTER TABLE IF EXISTS ONLY public.inventory_assignment DROP CONSTRAINT IF EXISTS inventory_assignment_employee_id_3a23febf_fk_inventory;
ALTER TABLE IF EXISTS ONLY public.inventory_assignment DROP CONSTRAINT IF EXISTS inventory_assignment_device_id_b776296b_fk_inventory_device_id;
ALTER TABLE IF EXISTS ONLY public.inventory_assignment DROP CONSTRAINT IF EXISTS inventory_assignment_assigned_by_id_65a9fc0e_fk_accounts_;
ALTER TABLE IF EXISTS ONLY public.inventory_activitylog DROP CONSTRAINT IF EXISTS inventory_activitylog_user_id_e4a6413e_fk_accounts_user_id;
ALTER TABLE IF EXISTS ONLY public.django_admin_log DROP CONSTRAINT IF EXISTS django_admin_log_user_id_c564eba6_fk_accounts_user_id;
ALTER TABLE IF EXISTS ONLY public.django_admin_log DROP CONSTRAINT IF EXISTS django_admin_log_content_type_id_c4bce8eb_fk_django_co;
ALTER TABLE IF EXISTS ONLY public.auth_permission DROP CONSTRAINT IF EXISTS auth_permission_content_type_id_2f476e4b_fk_django_co;
ALTER TABLE IF EXISTS ONLY public.auth_group_permissions DROP CONSTRAINT IF EXISTS auth_group_permissions_group_id_b120cbf9_fk_auth_group_id;
ALTER TABLE IF EXISTS ONLY public.auth_group_permissions DROP CONSTRAINT IF EXISTS auth_group_permissio_permission_id_84c5c92e_fk_auth_perm;
ALTER TABLE IF EXISTS ONLY public.accounts_user_user_permissions DROP CONSTRAINT IF EXISTS accounts_user_user_p_user_id_e4f0a161_fk_accounts_;
ALTER TABLE IF EXISTS ONLY public.accounts_user_user_permissions DROP CONSTRAINT IF EXISTS accounts_user_user_p_permission_id_113bb443_fk_auth_perm;
ALTER TABLE IF EXISTS ONLY public.accounts_user_groups DROP CONSTRAINT IF EXISTS accounts_user_groups_user_id_52b62117_fk_accounts_user_id;
ALTER TABLE IF EXISTS ONLY public.accounts_user_groups DROP CONSTRAINT IF EXISTS accounts_user_groups_group_id_bd11a704_fk_auth_group_id;
DROP INDEX IF EXISTS public.inventory_notification_user_id_b5616c82;
DROP INDEX IF EXISTS public.inventory_employee_tc_kimlik_no_1dec2ad1_like;
DROP INDEX IF EXISTS public.inventory_employee_email_d80fd5f6_like;
DROP INDEX IF EXISTS public.inventory_employee_company_id_8bec41c0;
DROP INDEX IF EXISTS public.inventory_device_name_009b2458_like;
DROP INDEX IF EXISTS public.inventory_d_name_59f036_idx;
DROP INDEX IF EXISTS public.inventory_company_name_ac2fdca8_like;
DROP INDEX IF EXISTS public.inventory_assignment_returned_by_id_9ef8825a;
DROP INDEX IF EXISTS public.inventory_assignment_employee_id_3a23febf;
DROP INDEX IF EXISTS public.inventory_assignment_device_id_b776296b;
DROP INDEX IF EXISTS public.inventory_assignment_assigned_by_id_65a9fc0e;
DROP INDEX IF EXISTS public.inventory_activitylog_user_id_e4a6413e;
DROP INDEX IF EXISTS public.inventory_a_created_fcdbcb_idx;
DROP INDEX IF EXISTS public.django_session_session_key_c0390e0f_like;
DROP INDEX IF EXISTS public.django_session_expire_date_a5c62663;
DROP INDEX IF EXISTS public.django_admin_log_user_id_c564eba6;
DROP INDEX IF EXISTS public.django_admin_log_content_type_id_c4bce8eb;
DROP INDEX IF EXISTS public.auth_permission_content_type_id_2f476e4b;
DROP INDEX IF EXISTS public.auth_group_permissions_permission_id_84c5c92e;
DROP INDEX IF EXISTS public.auth_group_permissions_group_id_b120cbf9;
DROP INDEX IF EXISTS public.auth_group_name_a6ea08ec_like;
DROP INDEX IF EXISTS public.accounts_user_username_6088629e_like;
DROP INDEX IF EXISTS public.accounts_user_user_permissions_user_id_e4f0a161;
DROP INDEX IF EXISTS public.accounts_user_user_permissions_permission_id_113bb443;
DROP INDEX IF EXISTS public.accounts_user_groups_user_id_52b62117;
DROP INDEX IF EXISTS public.accounts_user_groups_group_id_bd11a704;
ALTER TABLE IF EXISTS ONLY public.inventory_notification DROP CONSTRAINT IF EXISTS inventory_notification_pkey;
ALTER TABLE IF EXISTS ONLY public.inventory_employee DROP CONSTRAINT IF EXISTS inventory_employee_user_id_key;
ALTER TABLE IF EXISTS ONLY public.inventory_employee DROP CONSTRAINT IF EXISTS inventory_employee_tc_kimlik_no_1dec2ad1_uniq;
ALTER TABLE IF EXISTS ONLY public.inventory_employee DROP CONSTRAINT IF EXISTS inventory_employee_pkey;
ALTER TABLE IF EXISTS ONLY public.inventory_employee DROP CONSTRAINT IF EXISTS inventory_employee_email_key;
ALTER TABLE IF EXISTS ONLY public.inventory_device DROP CONSTRAINT IF EXISTS inventory_device_pkey;
ALTER TABLE IF EXISTS ONLY public.inventory_device DROP CONSTRAINT IF EXISTS inventory_device_name_009b2458_uniq;
ALTER TABLE IF EXISTS ONLY public.inventory_company DROP CONSTRAINT IF EXISTS inventory_company_pkey;
ALTER TABLE IF EXISTS ONLY public.inventory_company DROP CONSTRAINT IF EXISTS inventory_company_name_key;
ALTER TABLE IF EXISTS ONLY public.inventory_assignment DROP CONSTRAINT IF EXISTS inventory_assignment_pkey;
ALTER TABLE IF EXISTS ONLY public.inventory_activitylog DROP CONSTRAINT IF EXISTS inventory_activitylog_pkey;
ALTER TABLE IF EXISTS ONLY public.django_session DROP CONSTRAINT IF EXISTS django_session_pkey;
ALTER TABLE IF EXISTS ONLY public.django_migrations DROP CONSTRAINT IF EXISTS django_migrations_pkey;
ALTER TABLE IF EXISTS ONLY public.django_content_type DROP CONSTRAINT IF EXISTS django_content_type_pkey;
ALTER TABLE IF EXISTS ONLY public.django_content_type DROP CONSTRAINT IF EXISTS django_content_type_app_label_model_76bd3d3b_uniq;
ALTER TABLE IF EXISTS ONLY public.django_admin_log DROP CONSTRAINT IF EXISTS django_admin_log_pkey;
ALTER TABLE IF EXISTS ONLY public.auth_permission DROP CONSTRAINT IF EXISTS auth_permission_pkey;
ALTER TABLE IF EXISTS ONLY public.auth_permission DROP CONSTRAINT IF EXISTS auth_permission_content_type_id_codename_01ab375a_uniq;
ALTER TABLE IF EXISTS ONLY public.auth_group DROP CONSTRAINT IF EXISTS auth_group_pkey;
ALTER TABLE IF EXISTS ONLY public.auth_group_permissions DROP CONSTRAINT IF EXISTS auth_group_permissions_pkey;
ALTER TABLE IF EXISTS ONLY public.auth_group_permissions DROP CONSTRAINT IF EXISTS auth_group_permissions_group_id_permission_id_0cd325b0_uniq;
ALTER TABLE IF EXISTS ONLY public.auth_group DROP CONSTRAINT IF EXISTS auth_group_name_key;
ALTER TABLE IF EXISTS ONLY public.accounts_user DROP CONSTRAINT IF EXISTS accounts_user_username_key;
ALTER TABLE IF EXISTS ONLY public.accounts_user_user_permissions DROP CONSTRAINT IF EXISTS accounts_user_user_permissions_pkey;
ALTER TABLE IF EXISTS ONLY public.accounts_user_user_permissions DROP CONSTRAINT IF EXISTS accounts_user_user_permi_user_id_permission_id_2ab516c2_uniq;
ALTER TABLE IF EXISTS ONLY public.accounts_user DROP CONSTRAINT IF EXISTS accounts_user_pkey;
ALTER TABLE IF EXISTS ONLY public.accounts_user_groups DROP CONSTRAINT IF EXISTS accounts_user_groups_user_id_group_id_59c0b32f_uniq;
ALTER TABLE IF EXISTS ONLY public.accounts_user_groups DROP CONSTRAINT IF EXISTS accounts_user_groups_pkey;
DROP TABLE IF EXISTS public.inventory_notification;
DROP TABLE IF EXISTS public.inventory_employee;
DROP TABLE IF EXISTS public.inventory_device;
DROP TABLE IF EXISTS public.inventory_company;
DROP TABLE IF EXISTS public.inventory_assignment;
DROP TABLE IF EXISTS public.inventory_activitylog;
DROP TABLE IF EXISTS public.django_session;
DROP TABLE IF EXISTS public.django_migrations;
DROP TABLE IF EXISTS public.django_content_type;
DROP TABLE IF EXISTS public.django_admin_log;
DROP TABLE IF EXISTS public.auth_permission;
DROP TABLE IF EXISTS public.auth_group_permissions;
DROP TABLE IF EXISTS public.auth_group;
DROP TABLE IF EXISTS public.accounts_user_user_permissions;
DROP TABLE IF EXISTS public.accounts_user_groups;
DROP TABLE IF EXISTS public.accounts_user;
-- *not* dropping schema, since initdb creates it
--
-- Name: public; Type: SCHEMA; Schema: -; Owner: -
--

-- *not* creating schema, since initdb creates it


--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON SCHEMA public IS '';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: accounts_user; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.accounts_user (
    id bigint NOT NULL,
    password character varying(128) NOT NULL,
    last_login timestamp with time zone,
    is_superuser boolean NOT NULL,
    username character varying(150) NOT NULL,
    first_name character varying(150) NOT NULL,
    last_name character varying(150) NOT NULL,
    email character varying(254) NOT NULL,
    is_staff boolean NOT NULL,
    is_active boolean NOT NULL,
    date_joined timestamp with time zone NOT NULL,
    role character varying(10) NOT NULL,
    phone_number character varying(20) NOT NULL,
    last_seen timestamp with time zone,
    must_change_password boolean NOT NULL
);


--
-- Name: accounts_user_groups; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.accounts_user_groups (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    group_id integer NOT NULL
);


--
-- Name: accounts_user_groups_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.accounts_user_groups ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.accounts_user_groups_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: accounts_user_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.accounts_user ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.accounts_user_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: accounts_user_user_permissions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.accounts_user_user_permissions (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    permission_id integer NOT NULL
);


--
-- Name: accounts_user_user_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.accounts_user_user_permissions ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.accounts_user_user_permissions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: auth_group; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.auth_group (
    id integer NOT NULL,
    name character varying(150) NOT NULL
);


--
-- Name: auth_group_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.auth_group ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_group_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: auth_group_permissions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.auth_group_permissions (
    id bigint NOT NULL,
    group_id integer NOT NULL,
    permission_id integer NOT NULL
);


--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.auth_group_permissions ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_group_permissions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: auth_permission; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.auth_permission (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    content_type_id integer NOT NULL,
    codename character varying(100) NOT NULL
);


--
-- Name: auth_permission_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.auth_permission ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_permission_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: django_admin_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.django_admin_log (
    id integer NOT NULL,
    action_time timestamp with time zone NOT NULL,
    object_id text,
    object_repr character varying(200) NOT NULL,
    action_flag smallint NOT NULL,
    change_message text NOT NULL,
    content_type_id integer,
    user_id bigint NOT NULL,
    CONSTRAINT django_admin_log_action_flag_check CHECK ((action_flag >= 0))
);


--
-- Name: django_admin_log_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.django_admin_log ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.django_admin_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: django_content_type; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.django_content_type (
    id integer NOT NULL,
    app_label character varying(100) NOT NULL,
    model character varying(100) NOT NULL
);


--
-- Name: django_content_type_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.django_content_type ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.django_content_type_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: django_migrations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.django_migrations (
    id bigint NOT NULL,
    app character varying(255) NOT NULL,
    name character varying(255) NOT NULL,
    applied timestamp with time zone NOT NULL
);


--
-- Name: django_migrations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.django_migrations ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.django_migrations_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: django_session; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.django_session (
    session_key character varying(40) NOT NULL,
    session_data text NOT NULL,
    expire_date timestamp with time zone NOT NULL
);


--
-- Name: inventory_activitylog; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.inventory_activitylog (
    id bigint NOT NULL,
    action_type character varying(20) NOT NULL,
    description character varying(255) NOT NULL,
    ip_address inet,
    created_at timestamp with time zone NOT NULL,
    user_id bigint
);


--
-- Name: inventory_activitylog_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.inventory_activitylog ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.inventory_activitylog_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: inventory_assignment; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.inventory_assignment (
    id bigint NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    assigned_date date NOT NULL,
    expected_return_date date,
    returned_date date,
    notes text NOT NULL,
    return_notes text NOT NULL,
    returned boolean NOT NULL,
    assigned_by_id bigint,
    returned_by_id bigint,
    device_id bigint NOT NULL,
    employee_id bigint NOT NULL,
    return_condition character varying(20) NOT NULL,
    damage_description text NOT NULL
);


--
-- Name: inventory_assignment_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.inventory_assignment ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.inventory_assignment_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: inventory_company; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.inventory_company (
    id bigint NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    name character varying(100) NOT NULL
);


--
-- Name: inventory_company_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.inventory_company ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.inventory_company_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: inventory_device; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.inventory_device (
    id bigint NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    name character varying(150) NOT NULL,
    total_quantity integer NOT NULL,
    CONSTRAINT inventory_device_total_quantity_check CHECK ((total_quantity >= 0))
);


--
-- Name: inventory_device_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.inventory_device ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.inventory_device_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: inventory_employee; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.inventory_employee (
    id bigint NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    first_name character varying(50) NOT NULL,
    last_name character varying(50) NOT NULL,
    email character varying(254) NOT NULL,
    profile_photo character varying(100),
    is_active boolean NOT NULL,
    user_id bigint,
    tc_kimlik_no character varying(11) NOT NULL,
    hire_date date NOT NULL,
    company_id bigint NOT NULL
);


--
-- Name: inventory_employee_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.inventory_employee ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.inventory_employee_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: inventory_notification; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.inventory_notification (
    id bigint NOT NULL,
    title character varying(150) NOT NULL,
    message character varying(255) NOT NULL,
    link character varying(255) NOT NULL,
    is_read boolean NOT NULL,
    created_at timestamp with time zone NOT NULL,
    user_id bigint NOT NULL
);


--
-- Name: inventory_notification_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.inventory_notification ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.inventory_notification_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Data for Name: accounts_user; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.accounts_user (id, password, last_login, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined, role, phone_number, last_seen, must_change_password) FROM stdin;
5	pbkdf2_sha256$870000$uknnFvunX5hlQ2MpkZVWln$XKOvE8SLxXyiqu3vghdFreeiZPF91VOTloHiQPboIyU=	\N	f	mehmet			mehmet@gmail.com	f	t	2026-07-14 14:55:10.157195+03	staff		\N	f
1	pbkdf2_sha256$870000$7yaCZF6UHZfxvVgJvJpxMs$5wqy2WcuHSfmRer3K5FGV/kjp845UL7VkBVVgcXScSo=	2026-07-17 09:54:46.075808+03	t	beril	Beril	Kahramanca	beril@gmail.com	t	t	2026-07-14 13:51:45.874491+03	admin		2026-07-17 09:54:46.183356+03	f
6	pbkdf2_sha256$870000$A8ZitLsjduyigZvxyJXP4a$Izq4DRb0uUcBHPVCCIJ42Xhp8PV0clUeFBnYxWdTAMs=	\N	f	fatma			fatma@gmail.com	f	t	2026-07-14 14:55:46.175443+03	staff		\N	f
8	pbkdf2_sha256$870000$YxUmgOeabpc7qoNi9jblbu$uiTMMiZ6nVKcW8nc0c6nxweeY/mmLSv7QqwWvoUK5Dc=	\N	f	elif			elif@gmail.com	f	t	2026-07-14 14:56:44.214578+03	staff		\N	f
9	pbkdf2_sha256$870000$UUMBY5XlsExMXU1xvvjnUC$tCa2itz6L1JILlEAn1qfxuhJ7Ts8kUgWwx6Vdg/ukAE=	\N	f	can			can@gmail.com	f	t	2026-07-14 14:57:26.130481+03	staff		\N	f
41	pbkdf2_sha256$870000$BvSwkH0ZL2r4PN19hcWKgc$DlJtlaLR74+OKPJFWCTeXkvSJFSk+WmikV9yivJ9ekw=	2026-07-16 17:26:32.552011+03	f	hasan@gmail.com	hasan	kaynak	hasan@gmail.com	f	t	2026-07-16 17:26:16.475392+03	staff		2026-07-16 17:26:47.963325+03	f
7	pbkdf2_sha256$870000$AYZxK5g8BeEkEsMgysubdU$LgXnpv2EZu3j0o/LAS50IkuFDJwo9CaWIYr5A/Fgoew=	2026-07-17 08:15:01.385243+03	f	ahmet			ahmet@gmail.com	f	t	2026-07-14 14:56:09.326884+03	staff		2026-07-17 08:15:01.396544+03	f
10	pbkdf2_sha256$870000$PhctvZDWa2QKRngrov67bL$/lVgRFto9AzLsO8Wlmew7Pjue3lcrBNXuZ/Epq8amO0=	\N	f	emre			emre@gmail.com	f	t	2026-07-14 14:57:45.663857+03	staff		\N	f
2	pbkdf2_sha256$870000$6kqTyT8xyl4JojZdtozUcv$KVksCEf5oviNpfGHRxHMj9xWQp3gK3MYsJZaXy/GZeM=	2026-07-17 09:27:03.796544+03	t	mustafa	Mustafa	Yenidoğan	mustafa@gmail.com	t	t	2026-07-14 14:08:03.295038+03	staff		2026-07-17 09:27:22.623873+03	f
40	pbkdf2_sha256$870000$mPZEF6M9XyhuATOa5OzuuU$3OJAtivqFAZqvy8Ugxhntct80fEO9q7fvp2HqQgP1eA=	2026-07-16 17:12:08.843971+03	f	doga@gmail.com	Doğa	Uslu	doga@gmail.com	f	t	2026-07-16 17:11:53.726197+03	staff		2026-07-16 17:12:48.905191+03	f
4	pbkdf2_sha256$870000$WBWAlHZPYSMDNsKSQ2pZXa$u4jpN2PmbIInVE0r/iErd0syHzSBCF4dd4ILihipqpU=	\N	f	ayşe			ayse@gmail.com	f	t	2026-07-14 14:54:36.868993+03	staff		\N	f
39	pbkdf2_sha256$870000$uKTmIGmiauSe6BHUru2054$WR0mdC7kHjJQwIfBKvU2t4O9rdbMfdi+IteYgMMK75s=	2026-07-16 17:27:05.495985+03	f	mustafa1@gmail.com	mustafa	Doğan	mustafa1@gmail.com	f	t	2026-07-16 17:06:49.280759+03	staff		2026-07-16 17:27:08.834204+03	f
42	pbkdf2_sha256$870000$CfsmBt2dMFWg5ZL5WRxlSi$OUvUoG9e4CKPowABuO7t92ewtxpM2oYICIcZlNdd+Dk=	2026-07-16 17:29:52.133921+03	f	husnu@gmail.com	hüsnü	hüsnü	husnu@gmail.com	f	t	2026-07-16 17:29:34.632495+03	staff		2026-07-16 17:30:49.961206+03	f
35	pbkdf2_sha256$870000$DDTRJ7E7SgOFPzsFnmSEQn$cOD3zqzwNsSF3iZtkMOJCCIS0VKKe8+S7prX8p08iFA=	2026-07-16 16:36:54.76546+03	f	fatih	Fatih	Üret	fatih@gmail.com	f	t	2026-07-16 16:36:38.099922+03	staff		2026-07-16 16:37:40.004659+03	f
\.


--
-- Data for Name: accounts_user_groups; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.accounts_user_groups (id, user_id, group_id) FROM stdin;
\.


--
-- Data for Name: accounts_user_user_permissions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.accounts_user_user_permissions (id, user_id, permission_id) FROM stdin;
\.


--
-- Data for Name: auth_group; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.auth_group (id, name) FROM stdin;
\.


--
-- Data for Name: auth_group_permissions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.auth_group_permissions (id, group_id, permission_id) FROM stdin;
\.


--
-- Data for Name: auth_permission; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.auth_permission (id, name, content_type_id, codename) FROM stdin;
1	Can add log entry	1	add_logentry
2	Can change log entry	1	change_logentry
3	Can delete log entry	1	delete_logentry
4	Can view log entry	1	view_logentry
5	Can add permission	2	add_permission
6	Can change permission	2	change_permission
7	Can delete permission	2	delete_permission
8	Can view permission	2	view_permission
9	Can add group	3	add_group
10	Can change group	3	change_group
11	Can delete group	3	delete_group
12	Can view group	3	view_group
13	Can add content type	4	add_contenttype
14	Can change content type	4	change_contenttype
15	Can delete content type	4	delete_contenttype
16	Can view content type	4	view_contenttype
17	Can add session	5	add_session
18	Can change session	5	change_session
19	Can delete session	5	delete_session
20	Can view session	5	view_session
21	Can add Kullanici	6	add_user
22	Can change Kullanici	6	change_user
23	Can delete Kullanici	6	delete_user
24	Can view Kullanici	6	view_user
25	Can add Marka	7	add_brand
26	Can change Marka	7	change_brand
27	Can delete Marka	7	delete_brand
28	Can view Marka	7	view_brand
29	Can add Departman	8	add_department
30	Can change Departman	8	change_department
31	Can delete Departman	8	delete_department
32	Can view Departman	8	view_department
33	Can add Cihaz Kategorisi	9	add_devicecategory
34	Can change Cihaz Kategorisi	9	change_devicecategory
35	Can delete Cihaz Kategorisi	9	delete_devicecategory
36	Can view Cihaz Kategorisi	9	view_devicecategory
37	Can add Cihaz	10	add_device
38	Can change Cihaz	10	change_device
39	Can delete Cihaz	10	delete_device
40	Can view Cihaz	10	view_device
41	Can add Calisan	11	add_employee
42	Can change Calisan	11	change_employee
43	Can delete Calisan	11	delete_employee
44	Can view Calisan	11	view_employee
45	Can add Zimmet	12	add_assignment
46	Can change Zimmet	12	change_assignment
47	Can delete Zimmet	12	delete_assignment
48	Can view Zimmet	12	view_assignment
49	Can add Bakim Kaydi	13	add_maintenance
50	Can change Bakim Kaydi	13	change_maintenance
51	Can delete Bakim Kaydi	13	delete_maintenance
52	Can view Bakim Kaydi	13	view_maintenance
53	Can add Bildirim	14	add_notification
54	Can change Bildirim	14	change_notification
55	Can delete Bildirim	14	delete_notification
56	Can view Bildirim	14	view_notification
57	Can add Sistem Hareketi	15	add_activitylog
58	Can change Sistem Hareketi	15	change_activitylog
59	Can delete Sistem Hareketi	15	delete_activitylog
60	Can view Sistem Hareketi	15	view_activitylog
61	Can add Sirket	16	add_company
62	Can change Sirket	16	change_company
63	Can delete Sirket	16	delete_company
64	Can view Sirket	16	view_company
\.


--
-- Data for Name: django_admin_log; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.django_admin_log (id, action_time, object_id, object_repr, action_flag, change_message, content_type_id, user_id) FROM stdin;
1	2026-07-14 14:53:32.339232+03	3	Beril	3		6	2
2	2026-07-14 14:54:37.041227+03	4	ayşe	1	[{"added": {}}]	6	2
3	2026-07-14 14:55:10.32761+03	5	mehmet	1	[{"added": {}}]	6	2
4	2026-07-14 14:55:18.749158+03	5	mehmet	2	[]	6	2
5	2026-07-14 14:55:46.347403+03	6	fatma	1	[{"added": {}}]	6	2
6	2026-07-14 14:56:09.492823+03	7	ahmet	1	[{"added": {}}]	6	2
7	2026-07-14 14:56:44.385526+03	8	elif	1	[{"added": {}}]	6	2
8	2026-07-14 14:57:26.296705+03	9	can	1	[{"added": {}}]	6	2
9	2026-07-14 14:57:45.83278+03	10	emre	1	[{"added": {}}]	6	2
10	2026-07-14 15:45:11.954536+03	1	İnsan Kaynakları	1	[{"added": {}}]	8	2
11	2026-07-14 15:45:44.512714+03	2	Bilgi Teknolojileri	1	[{"added": {}}]	8	2
12	2026-07-14 15:46:01.19942+03	3	Muhasebe	1	[{"added": {}}]	8	2
13	2026-07-14 15:46:07.635776+03	4	Satın Alma	1	[{"added": {}}]	8	2
14	2026-07-14 15:46:11.812393+03	5	Üretim	1	[{"added": {}}]	8	2
15	2026-07-14 15:46:17.807477+03	6	Kalite Kontrol	1	[{"added": {}}]	8	2
16	2026-07-14 15:46:22.617794+03	7	Ar-Ge	1	[{"added": {}}]	8	2
17	2026-07-14 15:46:28.323698+03	8	Lojistik	1	[{"added": {}}]	8	2
18	2026-07-14 15:47:19.607904+03	1	Ayşe Demir	1	[{"added": {}}]	11	2
19	2026-07-14 15:47:46.035678+03	2	Mehmet Kaya	1	[{"added": {}}]	11	2
20	2026-07-14 15:48:15.540107+03	3	Fatma Çelik	1	[{"added": {}}]	11	2
21	2026-07-14 15:48:50.652884+03	4	Ahmet Şahin	1	[{"added": {}}]	11	2
22	2026-07-14 15:49:17.125052+03	5	Elif Arslan	1	[{"added": {}}]	11	2
23	2026-07-14 15:49:49.94981+03	6	Can Korkmaz	1	[{"added": {}}]	11	2
24	2026-07-14 15:50:21.756446+03	7	Emre Aydın	1	[{"added": {}}]	11	2
25	2026-07-14 15:51:56.426741+03	8	Mustafa Yenidoğan	1	[{"added": {}}]	11	2
\.


--
-- Data for Name: django_content_type; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.django_content_type (id, app_label, model) FROM stdin;
1	admin	logentry
2	auth	permission
3	auth	group
4	contenttypes	contenttype
5	sessions	session
6	accounts	user
7	inventory	brand
8	inventory	department
9	inventory	devicecategory
10	inventory	device
11	inventory	employee
12	inventory	assignment
13	inventory	maintenance
14	inventory	notification
15	inventory	activitylog
16	inventory	company
\.


--
-- Data for Name: django_migrations; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.django_migrations (id, app, name, applied) FROM stdin;
1	contenttypes	0001_initial	2026-07-14 13:51:18.821768+03
2	contenttypes	0002_remove_content_type_name	2026-07-14 13:51:18.823759+03
3	auth	0001_initial	2026-07-14 13:51:18.838497+03
4	auth	0002_alter_permission_name_max_length	2026-07-14 13:51:18.840075+03
5	auth	0003_alter_user_email_max_length	2026-07-14 13:51:18.841194+03
6	auth	0004_alter_user_username_opts	2026-07-14 13:51:18.84224+03
7	auth	0005_alter_user_last_login_null	2026-07-14 13:51:18.843733+03
8	auth	0006_require_contenttypes_0002	2026-07-14 13:51:18.844109+03
9	auth	0007_alter_validators_add_error_messages	2026-07-14 13:51:18.84578+03
10	auth	0008_alter_user_username_max_length	2026-07-14 13:51:18.847088+03
11	auth	0009_alter_user_last_name_max_length	2026-07-14 13:51:18.848327+03
12	auth	0010_alter_group_name_max_length	2026-07-14 13:51:18.850567+03
13	auth	0011_update_proxy_permissions	2026-07-14 13:51:18.851747+03
14	auth	0012_alter_user_first_name_max_length	2026-07-14 13:51:18.852775+03
15	accounts	0001_initial	2026-07-14 13:51:18.86913+03
16	admin	0001_initial	2026-07-14 13:51:18.877222+03
17	admin	0002_logentry_remove_auto_add	2026-07-14 13:51:18.879488+03
18	admin	0003_logentry_add_action_flag_choices	2026-07-14 13:51:18.881127+03
19	inventory	0001_initial	2026-07-14 13:51:18.958235+03
20	sessions	0001_initial	2026-07-14 13:51:18.962154+03
21	inventory	0002_employee_tc_hire_date_assignment_return_condition	2026-07-16 09:26:49.283622+03
22	inventory	0003_company_employee_company	2026-07-16 11:15:15.312351+03
23	inventory	0004_device_stock_fields	2026-07-16 11:17:28.634906+03
24	inventory	0005_device_stock_data	2026-07-16 11:17:28.654728+03
25	inventory	0006_device_stock_cleanup	2026-07-16 11:17:28.689346+03
26	inventory	0007_remove_legacy_models	2026-07-16 11:17:28.706894+03
27	accounts	0002_user_must_change_password	2026-07-16 16:29:38.717416+03
\.


--
-- Data for Name: django_session; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.django_session (session_key, session_data, expire_date) FROM stdin;
5hajean70waxxgkzpbgugvck7t45djje	.eJxVi8EKwyAQRP_Fc5Hoqht7LPTYb5CNbjA0TUKNp9J_r4UcWpjD8GbeSwSqew618DNMSZyFEqdfNlC88_IdaNuKpBjXuuxFHrzI64Om-bYmni_H9c_PVHKTAb2HkZJGB614MJ2LBsFilwAYrAIcvQbN2DtGUL0HYktOu8G0iPcHb7w1-A:1wkauC:TGLqJWGuxUZfGN1180K2UH8itkZWX16vy4tAv6_4dSg	2026-07-31 08:14:36.946379+03
z20stl6jl76ri90n9fqbzajfl2ao5gt1	.eJxVjL0KgzAUhd8lcxGTm-SajoWOpVPncE2uKNUoRqfSd28KDi2c4fCdn5fwtG-93zOvfojiLKQ4_bKWwpPTN6BlyRWFMO9py9XBc3WdaBjv66OUE018myOPl2P099RT7ssNoHPQUVRooRgHurZBIxisIwCDkYCdU6AYG8sIsnFAbMgq2-oi8f4AEqU5-Q:1wkFnW:d7J180mf_IJHTr8qyhG5Bmu95NJO3mtkNWR7DdCYU_0	2026-07-30 09:42:18.438605+03
mk6vrdsotm9kwn7999g9a6fjzyp17dc8	.eJxVjL0KgzAUhd8lcxGTm-SajoWOpVPncE2uKNUoRqfSd28KDi2c4fCdn5fwtG-93zOvfojiLKQ4_bKWwpPTN6BlyRWFMO9py9XBc3WdaBjv66OUE018myOPl2P099RT7ssNoHPQUVRooRgHurZBIxisIwCDkYCdU6AYG8sIsnFAbMgq2-oi8f4AEqU5-Q:1wkFo8:ofIAbsPh__Ta94EuvcW3R5xvj6JjSGNZUJNl54c5cHU	2026-07-30 09:42:56.990119+03
h4th9jbrld4a5cl2xfvteg3w74jtz0mj	.eJxVjL0KwjAURt8ls5T82SQdBUdxcg43zQ0N1rT0tqCI724LHXQ933fOm3lY5s4vhJPPkTVMssMvC9DesWwDjCNV0LbDUmaqdk7V-QG5v0639VzggZchYn_apb9SB9StGW2xjoZztE7ryF0yQUUtQgRUqU7OKq5Q2xhk4s5IIYKQyUonjtHUALBFCYnyUDw-xzy9WMM_XzcHQp8:1wjbav:HkYeC1tbfGWKU_52UxWvmx0eBmPVYyXjs8A4pJcjwW0	2026-07-28 14:46:37.080972+03
kjqvxs4b14l1cuvjlmhzw7n0493mrf8g	.eJxVjL0KgzAUhd8lcxGTm-SajoWOpVPncE2uKNUoRqfSd28KDi2c4fCdn5fwtG-93zOvfojiLKQ4_bKWwpPTN6BlyRWFMO9py9XBc3WdaBjv66OUE018myOPl2P099RT7ssNoHPQUVRooRgHurZBIxisIwCDkYCdU6AYG8sIsnFAbMgq2-oi8f4AEqU5-Q:1wkJPT:smeoQWvZ1bkf2mTnazFmQf9KMNmOhUGXGdr9tHvArWc	2026-07-30 13:33:43.284977+03
51nh7mi4mqp2x0i9867dtwpmqpt531ew	.eJxVjL0KgzAUhd8lcxGTm-SajoWOpVPncE2uKNUoRqfSd28KDi2c4fCdn5fwtG-93zOvfojiLKQ4_bKWwpPTN6BlyRWFMO9py9XBc3WdaBjv66OUE018myOPl2P099RT7ssNoHPQUVRooRgHurZBIxisIwCDkYCdU6AYG8sIsnFAbMgq2-oi8f4AEqU5-Q:1wkJPx:lHstqwz2GpbGU9RaJGKpHkSoqBDYI9lOqR3fCjIoEMY	2026-07-30 13:34:13.013255+03
kdjllitdkgavnwk06b6hib4tju36m7k7	.eJxVjL0KgzAUhd8lcxGTm-SajoWOpVPncE2uKNUoRqfSd28KDi2c4fCdn5fwtG-93zOvfojiLKQ4_bKWwpPTN6BlyRWFMO9py9XBc3WdaBjv66OUE018myOPl2P099RT7ssNoHPQUVRooRgHurZBIxisIwCDkYCdU6AYG8sIsnFAbMgq2-oi8f4AEqU5-Q:1wkJUN:prd5SiRssrNN3OCfElrYV__OKRh8s2nvEUTYEHKI1B4	2026-07-30 13:38:47.79867+03
aput2uo4bviz6dxzurew06h8kna9m0u1	.eJxVjL0KgzAUhd8lcxGTm-SajoWOpVPncE2uKNUoRqfSd28KDi2c4fCdn5fwtG-93zOvfojiLKQ4_bKWwpPTN6BlyRWFMO9py9XBc3WdaBjv66OUE018myOPl2P099RT7ssNoHPQUVRooRgHurZBIxisIwCDkYCdU6AYG8sIsnFAbMgq2-oi8f4AEqU5-Q:1wkJVM:pSx8o1F5Q8rgZCu414GS3VtjKWsa67X9HBYEnehQ0e0	2026-07-30 13:39:48.760791+03
rtxxjglrmzr07s6d4pgvp9g7amp1dw6t	.eJxVjL0KgzAUhd8lcxGTm-SajoWOpVPncE2uKNUoRqfSd28KDi2c4fCdn5fwtG-93zOvfojiLKQ4_bKWwpPTN6BlyRWFMO9py9XBc3WdaBjv66OUE018myOPl2P099RT7ssNoHPQUVRooRgHurZBIxisIwCDkYCdU6AYG8sIsnFAbMgq2-oi8f4AEqU5-Q:1wjdrF:By0isDNi_KZ8_f-qLFc4ZM7xkEACUoBbVMgl06PVOUk	2026-07-28 17:11:37.845808+03
62uarzx6xguwk8uwg5de1me400ff7v8b	.eJxVjL0KgzAUhd8lcxGTm-SajoWOpVPncE2uKNUoRqfSd28KDi2c4fCdn5fwtG-93zOvfojiLKQ4_bKWwpPTN6BlyRWFMO9py9XBc3WdaBjv66OUE018myOPl2P099RT7ssNoHPQUVRooRgHurZBIxisIwCDkYCdU6AYG8sIsnFAbMgq2-oi8f4AEqU5-Q:1wjdrO:CP8AoV-s1uekRJHH8KCvvLuB88kP_cKCJBaQrCBBc0c	2026-07-28 17:11:46.836929+03
z7n34ct9768w0lm5i06l072w1jhiieue	.eJxVjL0KgzAUhd8lcxGTm-SajoWOpVPncE2uKNUoRqfSd28KDi2c4fCdn5fwtG-93zOvfojiLKQ4_bKWwpPTN6BlyRWFMO9py9XBc3WdaBjv66OUE018myOPl2P099RT7ssNoHPQUVRooRgHurZBIxisIwCDkYCdU6AYG8sIsnFAbMgq2-oi8f4AEqU5-Q:1wkL4g:Dv__oWGfGB94FjEmzAkyH72yAb354IIemHJY_0JCUs4	2026-07-30 15:20:22.152326+03
eav9e5hicnp5kzuplktf07rf82cpfidv	.eJxVjL0KgzAUhd8lcxGTm-SajoWOpVPncE2uKNUoRqfSd28KDi2c4fCdn5fwtG-93zOvfojiLKQ4_bKWwpPTN6BlyRWFMO9py9XBc3WdaBjv66OUE018myOPl2P099RT7ssNoHPQUVRooRgHurZBIxisIwCDkYCdU6AYG8sIsnFAbMgq2-oi8f4AEqU5-Q:1wkL4m:kfgurGTMKxTLrNhDyNQAQgcQdluKx7d5Dr-i1BH_8Xo	2026-07-30 15:20:28.75262+03
o30llzwnearynbwydq3gck9x4tcta489	.eJxVjL0KgzAUhd8lcxGTm-SajoWOpVPncE2uKNUoRqfSd28KDi2c4fCdn5fwtG-93zOvfojiLKQ4_bKWwpPTN6BlyRWFMO9py9XBc3WdaBjv66OUE018myOPl2P099RT7ssNoHPQUVRooRgHurZBIxisIwCDkYCdU6AYG8sIsnFAbMgq2-oi8f4AEqU5-Q:1wkLVM:Xh6P0S8bzzLP66fnwQ9WDoW9n21j-AmWeU7j1LDdI84	2026-07-30 15:47:56.428586+03
xxzx52vaocgvw8fcxa98cwwfx8lb481s	.eJxVjL0KgzAUhd8lcxGTm-SajoWOpVPncE2uKNUoRqfSd28KDi2c4fCdn5fwtG-93zOvfojiLKQ4_bKWwpPTN6BlyRWFMO9py9XBc3WdaBjv66OUE018myOPl2P099RT7ssNoHPQUVRooRgHurZBIxisIwCDkYCdU6AYG8sIsnFAbMgq2-oi8f4AEqU5-Q:1wkFAT:oW_iIfXD4mdQkPsTT7Q_Ub6Z5Uq9bSvfrHJH-6eJTug	2026-07-30 09:01:57.605629+03
6pybu36kxpkly2n8jptdvkqs4yg3hovc	.eJxVjL0KgzAUhd8lcxGTm-SajoWOpVPncE2uKNUoRqfSd28KDi2c4fCdn5fwtG-93zOvfojiLKQ4_bKWwpPTN6BlyRWFMO9py9XBc3WdaBjv66OUE018myOPl2P099RT7ssNoHPQUVRooRgHurZBIxisIwCDkYCdU6AYG8sIsnFAbMgq2-oi8f4AEqU5-Q:1wkLew:feyMlEHpoYGw3Fe-Fh7VlTaWf-6qNB0fi1XzGrZHgSg	2026-07-30 15:57:50.499324+03
tgm6bfi4540j0klai92fsk258p8octdj	.eJxVjL0KgzAUhd8lcxGTm-SajoWOpVPncE2uKNUoRqfSd28KDi2c4fCdn5fwtG-93zOvfojiLKQ4_bKWwpPTN6BlyRWFMO9py9XBc3WdaBjv66OUE018myOPl2P099RT7ssNoHPQUVRooRgHurZBIxisIwCDkYCdU6AYG8sIsnFAbMgq2-oi8f4AEqU5-Q:1wkFAa:dfySoowChQ5jom6JYXLYbg7m0sb6-9xIv9_2t-45sk0	2026-07-30 09:02:04.605508+03
hbvzpp8bshi3r800vyw0ox2bj5d8em92	.eJxVjL0KgzAUhd8lcxGTm-SajoWOpVPncE2uKNUoRqfSd28KDi2c4fCdn5fwtG-93zOvfojiLKQ4_bKWwpPTN6BlyRWFMO9py9XBc3WdaBjv66OUE018myOPl2P099RT7ssNoHPQUVRooRgHurZBIxisIwCDkYCdU6AYG8sIsnFAbMgq2-oi8f4AEqU5-Q:1wkJ3S:8v0mDDnSLxZp1Bt1Sj6Zcw6DF85fuQHpWLnERafQJEQ	2026-07-30 13:10:58.934316+03
sdsxi5mkvtjui7gsyhp8o0eome8jr4g2	.eJxVjL0KgzAUhd8lcxGTm-SajoWOpVPncE2uKNUoRqfSd28KDi2c4fCdn5fwtG-93zOvfojiLKQ4_bKWwpPTN6BlyRWFMO9py9XBc3WdaBjv66OUE018myOPl2P099RT7ssNoHPQUVRooRgHurZBIxisIwCDkYCdU6AYG8sIsnFAbMgq2-oi8f4AEqU5-Q:1wkLhw:Bj5Q98td2jYUFePIIQoPCe0PQ6l0NsKZwCGI5aJSqkE	2026-07-30 16:00:56.226751+03
nc14byvl6lfhkstak587qsed37hb7rh3	.eJxVjL0KgzAUhd8lcxGTm-SajoWOpVPncE2uKNUoRqfSd28KDi2c4fCdn5fwtG-93zOvfojiLKQ4_bKWwpPTN6BlyRWFMO9py9XBc3WdaBjv66OUE018myOPl2P099RT7ssNoHPQUVRooRgHurZBIxisIwCDkYCdU6AYG8sIsnFAbMgq2-oi8f4AEqU5-Q:1wkLjb:X8TNwNcxK9NSUDAtrtv3Snca2JgekBvSLHTznhpkINo	2026-07-30 16:02:39.280616+03
jkwrfvicnfy3cug4g2b9bekcr3mu8k6n	.eJxVjL0KgzAUhd8lcxGTm-SajoWOpVPncE2uKNUoRqfSd28KDi2c4fCdn5fwtG-93zOvfojiLKQ4_bKWwpPTN6BlyRWFMO9py9XBc3WdaBjv66OUE018myOPl2P099RT7ssNoHPQUVRooRgHurZBIxisIwCDkYCdU6AYG8sIsnFAbMgq2-oi8f4AEqU5-Q:1wkMAg:duDIGur2vdCE09J6kJRIX7nC4S5mvE243xAPSMFLa6A	2026-07-30 16:30:38.915688+03
agmzwc7rc3rs2pp4dcbcau5p3pcm1uv0	.eJxVjL0OwiAURt-F2ZBC-SmOJo7GyZlc4BIaW9qUMhnfXUw66HrO950XsVD3ZGvBzY6BnEnPyekXOvBPzF8D61ooeL_UvBd68EKvM4zTfXu0cYYZb0vA6XKc_koJSmoZNjg0vcNgtBrQRe0kk0Ipo1CzGARojb00XLjAfed9Eywq1SEIjsAkeX8AfrU71g:1wkMAh:bjh5h_21_tcj5hqKKZXl8B6iM4ue3c0_LOsgU3KK9os	2026-07-30 16:30:39.580207+03
wa6puycd8tgjfaijv7wp5m09oihfi44q	.eJxVjLkOwjAQBf_FNbJs45MSKSWioo5217YckUtxUiH-nSClgHbem3mxFra1tFtNS9tFdmFnxU6_EIGeafwuMM-VA9G0jWvlB6-8GaDr78tjP48wpNsUU389pL9SgVr2TEblVCKHUmaPQjsSJqAl0JZCJiWNNB6DRR21zY50sDEYABAhKWk9e38AgNM7yQ:1wkMAh:yHviBDAl3kDGn_w8s3Ax3yiP6829_pEG50bX9gxOOl0	2026-07-30 16:30:39.874926+03
hxv3ihsob0sk28kq9apdjbwizqyxwwgs	.eJxVjLEOgjAURf-lsyFtKbZ1NGE0Ts7Ne32PQIRCKEzGf7cmDLqee-55iQD71oc98xoGEhdhxemXIcQnp-8Ay5IriHHe05arg-eqnWAY7-ujyAkmvs3E4_U4_ZV6yH3JcI0SzozOKKUj1V2HCGikdU0k66WyFg35xqPxEb3WRZTKATJpR9SJ9wdoMjwb:1wkMB2:LROXjMFFfl4YPGdMCDlB5d0bJxJbvJQZWP-64XepLo0	2026-07-30 16:31:00.503455+03
v2mngqs2vq3fbsrj5afqxjk57cos2yhw	.eJxVjLEOgjAURf-lsyFtKbZ1NGE0Ts7Ne32PQIRCKEzGf7cmDLqee-55iQD71oc98xoGEhdhxemXIcQnp-8Ay5IriHHe05arg-eqnWAY7-ujyAkmvs3E4_U4_ZV6yH3JcI0SzozOKKUj1V2HCGikdU0k66WyFg35xqPxEb3WRZTKATJpR9SJ9wdoMjwb:1wkMBM:O7fuJzwBeoUEAfiycXQxKr9PGUtvJ4w_1fHQ9yDi_XE	2026-07-30 16:31:20.310621+03
nltdtmx529uxbo3nlj1j160l7u3sgskq	.eJxVjLEOgjAURf-lsyFtKbZ1NGE0Ts7Ne32PQIRCKEzGf7cmDLqee-55iQD71oc98xoGEhdhxemXIcQnp-8Ay5IriHHe05arg-eqnWAY7-ujyAkmvs3E4_U4_ZV6yH3JcI0SzozOKKUj1V2HCGikdU0k66WyFg35xqPxEb3WRZTKATJpR9SJ9wdoMjwb:1wkMBb:wL-7Cih23OuDgZE1ItL0bRWPWdE027aaLRrqjMOhWEA	2026-07-30 16:31:35.223662+03
jw4xgydnjgd0aftfx1yk8qzhckw32irr	.eJxVjL0KgzAUhd8lcxGTm-SajoWOpVPncE2uKNUoRqfSd28KDi2c4fCdn5fwtG-93zOvfojiLKQ4_bKWwpPTN6BlyRWFMO9py9XBc3WdaBjv66OUE018myOPl2P099RT7ssNoHPQUVRooRgHurZBIxisIwCDkYCdU6AYG8sIsnFAbMgq2-oi8f4AEqU5-Q:1wkMBv:iP9TXkABN2SWTo6CqggKSowVN4VAG5eMhSIHjhXt5E8	2026-07-30 16:31:55.588991+03
4ojp2nnzm17ttu74xkle89z0ydn5wwwt	.eJxVi70OwiAQgN-F2RCgVMDRxNFnIHfcERpr25QyGd_dmnTQ9ft5iQhtK7FVXuNA4iKcOP0yhPTg6StgWaqElOY2bVUevMrbE4bxPhOP1yP9-wvUss_coYIzo7dam0RdzoiAVjnfJ3JBaefQUugD2pAwGLOHSntAJuOJsnh_AMUNOBo:1wkauD:m7WVTO-qcb0Y5wZGC0XraQTwv7t3k9lo8eu8tDfcu6E	2026-07-31 08:14:37.071429+03
c87ujr28qiazu7ark2s9xht9pm1cgteu	.eJxVjL0KgzAUhd8lcxGTm-SajoWOpVPncE2uKNUoRqfSd28KDi2c4fCdn5fwtG-93zOvfojiLKQ4_bKWwpPTN6BlyRWFMO9py9XBc3WdaBjv66OUE018myOPl2P099RT7ssNoHPQUVRooRgHurZBIxisIwCDkYCdU6AYG8sIsnFAbMgq2-oi8f4AEqU5-Q:1wkME8:6WwoRpJ2JD9IO-seve50GVPX8Q_uWS0rjDt4rFmRQW0	2026-07-30 16:34:12.827037+03
c0fell4a1n9tk8e7sbozd6m1fmy4tnxw	.eJxVi8EKwyAQRP_Fc5Hoqht7LPTYb5CNbjA0TUKNp9J_r4UcWpjD8GbeSwSqew618DNMSZyFEqdfNlC88_IdaNuKpBjXuuxFHrzI64Om-bYmni_H9c_PVHKTAb2HkZJGB614MJ2LBsFilwAYrAIcvQbN2DtGUL0HYktOu8G0iPcHb7w1-A:1wkaub:l5zd9zBjiAoPVupz0axErskXP2oDf8gUMRstUfLaLTU	2026-07-31 08:15:01.284607+03
czcpe77ai91dlzrfkc1whf19gwwezrqx	.eJxVjLEOgjAURf-lsyFtKbZ1NGE0Ts7Ne32PQIRCKEzGf7cmDLqee-55iQD71oc98xoGEhdhxemXIcQnp-8Ay5IriHHe05arg-eqnWAY7-ujyAkmvs3E4_U4_ZV6yH3JcI0SzozOKKUj1V2HCGikdU0k66WyFg35xqPxEb3WRZTKATJpR9SJ9wdoMjwb:1wkME8:Zeajlrh0CHgudbRfafwUQM_wRH9unufe24vBBNeTt60	2026-07-30 16:34:12.920247+03
ussdvsf8vzg1m1lf4qj8hx3cebyac43m	.eJxVi70OwiAQgN-F2RCgVMDRxNFnIHfcERpr25QyGd_dmnTQ9ft5iQhtK7FVXuNA4iKcOP0yhPTg6StgWaqElOY2bVUevMrbE4bxPhOP1yP9-wvUss_coYIzo7dam0RdzoiAVjnfJ3JBaefQUugD2pAwGLOHSntAJuOJsnh_AMUNOBo:1wkaub:IntBonVwZ9DJXM40MDiB76bItN2yK6mvjikTirHRMB0	2026-07-31 08:15:01.386062+03
8kn7xr51zhpbeesm36q054e2h63mu10a	.eJxVjMEKgzAQRP8l5yKa1azxWPDYbwhrsmKo1eAqtJT-exU8tDCHYWbevJWjbR3cJry4GFSjCnX5zTryd56OglKSjLyft2mV7Mwlax8Ux9sceLye0z9-IBl2GNBa6CloNLAbC2VufIlQYR4AGKoCsLcaNGNtGKGoLRBXZLTpyl3HqbBInCfHzxSXl2ryzxfxYz01:1wkc33:hh7eU3svl6cNz0iq7fn6CpPaRkMXs7Zq1crUh6Ojqn0	2026-07-31 09:27:49.671439+03
pbbu7ankkft81pt39rkk46esmkh5m40q	.eJxVi8EKwyAQRP_Fc5Hoqht7LPTYb5CNbjA0TUKNp9J_r4UcWpjD8GbeSwSqew618DNMSZyFEqdfNlC88_IdaNuKpBjXuuxFHrzI64Om-bYmni_H9c_PVHKTAb2HkZJGB614MJ2LBsFilwAYrAIcvQbN2DtGUL0HYktOu8G0iPcHb7w1-A:1wkcT8:G7ODSguwfnCCOymHstxo7ubZZE3Qxsm6lgrur_reJfo	2026-07-31 09:54:46.077279+03
pomknf0lfa8wq7f7erjnz4k7jj23srs6	.eJxVjLEOgjAURf-lsyFtKbZ1NGE0Ts7Ne32PQIRCKEzGf7cmDLqee-55iQD71oc98xoGEhdhxemXIcQnp-8Ay5IriHHe05arg-eqnWAY7-ujyAkmvs3E4_U4_ZV6yH3JcI0SzozOKKUj1V2HCGikdU0k66WyFg35xqPxEb3WRZTKATJpR9SJ9wdoMjwb:1wkMVU:iMbl3_7aAXhIp7b-HbFu-enyP2OQJq6AH5_-JBasrgQ	2026-07-30 16:52:08.214386+03
denh4s1lyoev9s6qlls2b677nx5i8k1s	.eJxVjLEOgjAURf-lsyFtKbZ1NGE0Ts7Ne32PQIRCKEzGf7cmDLqee-55iQD71oc98xoGEhdhxemXIcQnp-8Ay5IriHHe05arg-eqnWAY7-ujyAkmvs3E4_U4_ZV6yH3JcI0SzozOKKUj1V2HCGikdU0k66WyFg35xqPxEb3WRZTKATJpR9SJ9wdoMjwb:1wkMfE:bM8NrcS6J26UBUDi3yMT5WRoETckHv4DRMPFiU50RtE	2026-07-30 17:02:12.446274+03
e2dx9yc5zp185n64gpcvqi4ueddtawfe	.eJxVjL0KgzAUhd8lcxGTm-SajoWOpVPncE2uKNUoRqfSd28KDi2c4fCdn5fwtG-93zOvfojiLKQ4_bKWwpPTN6BlyRWFMO9py9XBc3WdaBjv66OUE018myOPl2P099RT7ssNoHPQUVRooRgHurZBIxisIwCDkYCdU6AYG8sIsnFAbMgq2-oi8f4AEqU5-Q:1wkMff:tMFH0GFaEaXz0bc7GxPz3XoNZWViBEgFwLq0UfnVIU4	2026-07-30 17:02:39.294343+03
j5v737o6pcpmrqgfjnkj6dprhqvbg5gl	.eJxVjLEOgjAURf-lsyFtKbZ1NGE0Ts7Ne32PQIRCKEzGf7cmDLqee-55iQD71oc98xoGEhdhxemXIcQnp-8Ay5IriHHe05arg-eqnWAY7-ujyAkmvs3E4_U4_ZV6yH3JcI0SzozOKKUj1V2HCGikdU0k66WyFg35xqPxEb3WRZTKATJpR9SJ9wdoMjwb:1wkMff:VXiB7PkbR6Y8LdMHjPIBn-5xwE5OLoV050CiUurb2ZE	2026-07-30 17:02:39.40119+03
\.


--
-- Data for Name: inventory_activitylog; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.inventory_activitylog (id, action_type, description, ip_address, created_at, user_id) FROM stdin;
1	login	beril sisteme giris yapti.	127.0.0.1	2026-07-14 13:52:15.755737+03	1
2	logout	beril sistemden cikis yapti.	127.0.0.1	2026-07-14 13:52:26.067239+03	1
3	login	beril sisteme giris yapti.	127.0.0.1	2026-07-14 13:52:50.059636+03	1
4	other	Basarisiz giris denemesi: 'beril'	127.0.0.1	2026-07-14 14:08:25.688161+03	\N
5	login	beril sisteme giris yapti.	127.0.0.1	2026-07-14 14:08:31.173233+03	1
6	logout	beril sistemden cikis yapti.	127.0.0.1	2026-07-14 14:11:19.169354+03	1
7	login	mustafa sisteme giris yapti.	127.0.0.1	2026-07-14 14:11:29.609726+03	2
8	logout	mustafa sistemden cikis yapti.	127.0.0.1	2026-07-14 14:46:04.973563+03	2
9	other	Basarisiz giris denemesi: 'mustafa'	127.0.0.1	2026-07-14 14:46:24.838615+03	\N
10	login	mustafa sisteme giris yapti.	127.0.0.1	2026-07-14 14:46:37.079774+03	2
11	create	Departman: 'İnsan Kaynakları' olusturuldu.	127.0.0.1	2026-07-14 15:45:11.953268+03	2
12	create	Departman: 'Bilgi Teknolojileri' olusturuldu.	127.0.0.1	2026-07-14 15:45:44.512012+03	2
13	create	Departman: 'Muhasebe' olusturuldu.	127.0.0.1	2026-07-14 15:46:01.198641+03	2
14	create	Departman: 'Satın Alma' olusturuldu.	127.0.0.1	2026-07-14 15:46:07.634764+03	2
15	create	Departman: 'Üretim' olusturuldu.	127.0.0.1	2026-07-14 15:46:11.811716+03	2
16	create	Departman: 'Kalite Kontrol' olusturuldu.	127.0.0.1	2026-07-14 15:46:17.806927+03	2
17	create	Departman: 'Ar-Ge' olusturuldu.	127.0.0.1	2026-07-14 15:46:22.617147+03	2
18	create	Departman: 'Lojistik' olusturuldu.	127.0.0.1	2026-07-14 15:46:28.322889+03	2
19	create	Calisan: 'Ayşe Demir' olusturuldu.	127.0.0.1	2026-07-14 15:47:19.606807+03	2
20	create	Calisan: 'Mehmet Kaya' olusturuldu.	127.0.0.1	2026-07-14 15:47:46.035085+03	2
21	create	Calisan: 'Fatma Çelik' olusturuldu.	127.0.0.1	2026-07-14 15:48:15.538649+03	2
22	create	Calisan: 'Ahmet Şahin' olusturuldu.	127.0.0.1	2026-07-14 15:48:50.65229+03	2
23	create	Calisan: 'Elif Arslan' olusturuldu.	127.0.0.1	2026-07-14 15:49:17.123994+03	2
24	create	Calisan: 'Can Korkmaz' olusturuldu.	127.0.0.1	2026-07-14 15:49:49.948973+03	2
25	create	Calisan: 'Emre Aydın' olusturuldu.	127.0.0.1	2026-07-14 15:50:21.755499+03	2
26	create	Calisan: 'Mustafa Yenidoğan' olusturuldu.	127.0.0.1	2026-07-14 15:51:56.425647+03	2
27	login	mustafa sisteme giris yapti.	127.0.0.1	2026-07-14 16:30:07.660241+03	2
28	logout	mustafa sistemden cikis yapti.	127.0.0.1	2026-07-14 16:33:03.279764+03	2
29	login	mustafa sisteme giris yapti.	127.0.0.1	2026-07-14 16:33:10.842131+03	2
30	create	Cihaz Kategorisi: 'Laptop' olusturuldu.	\N	2026-07-14 16:39:32.701458+03	\N
31	create	Cihaz Kategorisi: 'Telefon' olusturuldu.	\N	2026-07-14 16:39:32.703596+03	\N
32	create	Cihaz Kategorisi: 'Tablet' olusturuldu.	\N	2026-07-14 16:39:32.704498+03	\N
33	create	Cihaz Kategorisi: 'Monitor' olusturuldu.	\N	2026-07-14 16:39:32.705428+03	\N
34	create	Cihaz Kategorisi: 'Yazici' olusturuldu.	\N	2026-07-14 16:39:32.706339+03	\N
35	create	Cihaz Kategorisi: 'Sunucu' olusturuldu.	\N	2026-07-14 16:39:32.707203+03	\N
36	create	Cihaz Kategorisi: 'Diger' olusturuldu.	\N	2026-07-14 16:39:32.708045+03	\N
37	create	Marka: 'HP' olusturuldu.	\N	2026-07-14 16:39:32.710408+03	\N
38	create	Marka: 'Dell' olusturuldu.	\N	2026-07-14 16:39:32.711392+03	\N
39	create	Marka: 'Lenovo' olusturuldu.	\N	2026-07-14 16:39:32.712209+03	\N
40	create	Marka: 'Apple' olusturuldu.	\N	2026-07-14 16:39:32.712996+03	\N
41	create	Marka: 'Asus' olusturuldu.	\N	2026-07-14 16:39:32.713715+03	\N
42	create	Marka: 'Samsung' olusturuldu.	\N	2026-07-14 16:39:32.714483+03	\N
43	create	Marka: 'Huawei' olusturuldu.	\N	2026-07-14 16:39:32.715204+03	\N
44	create	Marka: 'Acer' olusturuldu.	\N	2026-07-14 16:39:32.715914+03	\N
45	create	Cihaz: 'Lenovo Monitor Plus (ENV-0001)' olusturuldu.	\N	2026-07-14 16:39:32.720699+03	\N
46	create	Cihaz: 'Acer Diger Prime (ENV-0002)' olusturuldu.	\N	2026-07-14 16:39:34.096944+03	\N
47	create	Cihaz: 'HP Yazici Max (ENV-0003)' olusturuldu.	\N	2026-07-14 16:39:34.107472+03	\N
48	create	Cihaz: 'Lenovo Sunucu Max (ENV-0004)' olusturuldu.	\N	2026-07-14 16:39:34.114704+03	\N
49	create	Cihaz: 'Dell Sunucu Pro (ENV-0005)' olusturuldu.	\N	2026-07-14 16:39:34.122699+03	\N
50	create	Cihaz: 'Lenovo Yazici 2024 (ENV-0006)' olusturuldu.	\N	2026-07-14 16:39:34.130375+03	\N
51	create	Cihaz: 'Samsung Tablet Elite (ENV-0007)' olusturuldu.	\N	2026-07-14 16:39:34.138009+03	\N
52	create	Cihaz: 'Apple Sunucu Pro (ENV-0008)' olusturuldu.	\N	2026-07-14 16:39:34.145325+03	\N
53	create	Cihaz: 'Apple Laptop S (ENV-0009)' olusturuldu.	\N	2026-07-14 16:39:34.152856+03	\N
54	create	Cihaz: 'Acer Telefon Pro (ENV-0010)' olusturuldu.	\N	2026-07-14 16:39:34.159826+03	\N
55	create	Cihaz: 'Samsung Yazici Max (ENV-0011)' olusturuldu.	\N	2026-07-14 16:39:34.167753+03	\N
56	create	Cihaz: 'HP Sunucu Lite (ENV-0012)' olusturuldu.	\N	2026-07-14 16:39:34.175265+03	\N
57	create	Cihaz: 'HP Sunucu 2024 (ENV-0013)' olusturuldu.	\N	2026-07-14 16:39:34.182494+03	\N
58	create	Cihaz: 'Dell Sunucu X (ENV-0014)' olusturuldu.	\N	2026-07-14 16:39:34.189902+03	\N
59	create	Cihaz: 'Huawei Telefon S (ENV-0015)' olusturuldu.	\N	2026-07-14 16:39:34.197226+03	\N
60	create	Cihaz: 'Acer Yazici Pro (ENV-0016)' olusturuldu.	\N	2026-07-14 16:39:34.20426+03	\N
61	create	Cihaz: 'Asus Laptop S (ENV-0017)' olusturuldu.	\N	2026-07-14 16:39:34.211123+03	\N
62	create	Cihaz: 'Asus Diger Plus (ENV-0018)' olusturuldu.	\N	2026-07-14 16:39:34.217999+03	\N
63	create	Cihaz: 'Apple Tablet 2024 (ENV-0019)' olusturuldu.	\N	2026-07-14 16:39:34.225262+03	\N
64	create	Cihaz: 'Dell Diger Pro (ENV-0020)' olusturuldu.	\N	2026-07-14 16:39:34.231797+03	\N
65	create	Cihaz: 'Samsung Tablet 2024 (ENV-0021)' olusturuldu.	\N	2026-07-14 16:39:34.237896+03	\N
66	create	Cihaz: 'Acer Telefon Lite (ENV-0022)' olusturuldu.	\N	2026-07-14 16:39:34.244718+03	\N
67	create	Cihaz: 'Huawei Telefon Lite (ENV-0023)' olusturuldu.	\N	2026-07-14 16:39:34.250972+03	\N
68	create	Cihaz: 'Apple Diger Air (ENV-0024)' olusturuldu.	\N	2026-07-14 16:39:34.256741+03	\N
69	create	Cihaz: 'Dell Sunucu Elite (ENV-0025)' olusturuldu.	\N	2026-07-14 16:39:34.26267+03	\N
70	create	Cihaz: 'Apple Sunucu X (ENV-0026)' olusturuldu.	\N	2026-07-14 16:39:34.268438+03	\N
71	create	Cihaz: 'Asus Laptop X (ENV-0027)' olusturuldu.	\N	2026-07-14 16:39:34.274201+03	\N
72	create	Cihaz: 'Acer Diger X (ENV-0028)' olusturuldu.	\N	2026-07-14 16:39:34.279741+03	\N
73	create	Cihaz: 'Dell Monitor 2024 (ENV-0029)' olusturuldu.	\N	2026-07-14 16:39:34.285566+03	\N
74	create	Cihaz: 'Dell Sunucu X (ENV-0030)' olusturuldu.	\N	2026-07-14 16:39:34.291413+03	\N
75	create	Cihaz: 'Acer Yazici Lite (ENV-0031)' olusturuldu.	\N	2026-07-14 16:39:34.29667+03	\N
76	create	Cihaz: 'Lenovo Yazici X (ENV-0032)' olusturuldu.	\N	2026-07-14 16:39:34.302775+03	\N
77	create	Cihaz: 'Asus Sunucu 2024 (ENV-0033)' olusturuldu.	\N	2026-07-14 16:39:34.308213+03	\N
78	create	Cihaz: 'Lenovo Diger S (ENV-0034)' olusturuldu.	\N	2026-07-14 16:39:34.314327+03	\N
79	create	Cihaz: 'Asus Laptop Elite (ENV-0035)' olusturuldu.	\N	2026-07-14 16:39:34.32012+03	\N
80	create	Cihaz: 'HP Telefon X (ENV-0036)' olusturuldu.	\N	2026-07-14 16:39:34.325799+03	\N
81	create	Cihaz: 'HP Diger Prime (ENV-0037)' olusturuldu.	\N	2026-07-14 16:39:34.330922+03	\N
82	create	Cihaz: 'HP Diger Max (ENV-0038)' olusturuldu.	\N	2026-07-14 16:39:34.336615+03	\N
83	create	Cihaz: 'Lenovo Diger Lite (ENV-0039)' olusturuldu.	\N	2026-07-14 16:39:34.343349+03	\N
84	create	Cihaz: 'Apple Laptop Air (ENV-0040)' olusturuldu.	\N	2026-07-14 16:39:34.349056+03	\N
85	update	Cihaz: 'Lenovo Diger Lite (ENV-0039)' guncellendi.	\N	2026-07-14 16:39:34.363998+03	\N
86	assign	Lenovo Diger Lite (ENV-0039) cihazi Fatma Çelik adli calisana zimmetlendi.	\N	2026-07-14 16:39:34.368934+03	1
87	update	Cihaz: 'Dell Sunucu Pro (ENV-0005)' guncellendi.	\N	2026-07-14 16:39:34.375546+03	\N
88	assign	Dell Sunucu Pro (ENV-0005) cihazi Can Korkmaz adli calisana zimmetlendi.	\N	2026-07-14 16:39:34.379653+03	1
89	update	Cihaz: 'HP Diger Prime (ENV-0037)' guncellendi.	\N	2026-07-14 16:39:34.384066+03	\N
90	assign	HP Diger Prime (ENV-0037) cihazi Can Korkmaz adli calisana zimmetlendi.	\N	2026-07-14 16:39:34.388962+03	1
91	update	Cihaz: 'Samsung Yazici Max (ENV-0011)' guncellendi.	\N	2026-07-14 16:39:34.393028+03	\N
92	assign	Samsung Yazici Max (ENV-0011) cihazi Mustafa Yenidoğan adli calisana zimmetlendi.	\N	2026-07-14 16:39:34.397822+03	1
93	update	Cihaz: 'Samsung Tablet 2024 (ENV-0021)' guncellendi.	\N	2026-07-14 16:39:34.402285+03	\N
94	assign	Samsung Tablet 2024 (ENV-0021) cihazi Ahmet Şahin adli calisana zimmetlendi.	\N	2026-07-14 16:39:34.407205+03	1
95	update	Cihaz: 'HP Sunucu 2024 (ENV-0013)' guncellendi.	\N	2026-07-14 16:39:34.412217+03	\N
96	assign	HP Sunucu 2024 (ENV-0013) cihazi Mustafa Yenidoğan adli calisana zimmetlendi.	\N	2026-07-14 16:39:34.417118+03	1
97	update	Cihaz: 'Acer Diger Prime (ENV-0002)' guncellendi.	\N	2026-07-14 16:39:34.422186+03	\N
98	assign	Acer Diger Prime (ENV-0002) cihazi Fatma Çelik adli calisana zimmetlendi.	\N	2026-07-14 16:39:34.426446+03	1
99	update	Cihaz: 'Acer Telefon Pro (ENV-0010)' guncellendi.	\N	2026-07-14 16:39:34.430298+03	\N
100	assign	Acer Telefon Pro (ENV-0010) cihazi Ahmet Şahin adli calisana zimmetlendi.	\N	2026-07-14 16:39:34.435354+03	1
101	update	Cihaz: 'HP Sunucu Lite (ENV-0012)' guncellendi.	\N	2026-07-14 16:39:34.440097+03	\N
102	assign	HP Sunucu Lite (ENV-0012) cihazi Fatma Çelik adli calisana zimmetlendi.	\N	2026-07-14 16:39:34.445186+03	1
103	update	Cihaz: 'Apple Laptop S (ENV-0009)' guncellendi.	\N	2026-07-14 16:39:34.449702+03	\N
104	assign	Apple Laptop S (ENV-0009) cihazi Elif Arslan adli calisana zimmetlendi.	\N	2026-07-14 16:39:34.45403+03	1
105	update	Cihaz: 'Dell Sunucu X (ENV-0030)' guncellendi.	\N	2026-07-14 16:39:34.458678+03	\N
106	assign	Dell Sunucu X (ENV-0030) cihazi Can Korkmaz adli calisana zimmetlendi.	\N	2026-07-14 16:39:34.46353+03	1
107	update	Cihaz: 'Lenovo Yazici X (ENV-0032)' guncellendi.	\N	2026-07-14 16:39:34.468444+03	\N
108	assign	Lenovo Yazici X (ENV-0032) cihazi Mustafa Yenidoğan adli calisana zimmetlendi.	\N	2026-07-14 16:39:34.473353+03	1
109	update	Cihaz: 'Asus Laptop S (ENV-0017)' guncellendi.	\N	2026-07-14 16:39:34.477392+03	\N
110	assign	Asus Laptop S (ENV-0017) cihazi Elif Arslan adli calisana zimmetlendi.	\N	2026-07-14 16:39:34.482404+03	1
111	update	Cihaz: 'Samsung Tablet Elite (ENV-0007)' guncellendi.	\N	2026-07-14 16:39:34.48712+03	\N
112	assign	Samsung Tablet Elite (ENV-0007) cihazi Ayşe Demir adli calisana zimmetlendi.	\N	2026-07-14 16:39:34.491426+03	1
113	update	Cihaz: 'Dell Sunucu X (ENV-0014)' guncellendi.	\N	2026-07-14 16:39:34.495707+03	\N
114	assign	Dell Sunucu X (ENV-0014) cihazi Elif Arslan adli calisana zimmetlendi.	\N	2026-07-14 16:39:34.500633+03	1
115	logout	mustafa sistemden cikis yapti.	127.0.0.1	2026-07-14 16:41:14.809151+03	2
116	other	Basarisiz giris denemesi: 'admin'	127.0.0.1	2026-07-14 16:41:27.933662+03	\N
117	other	Basarisiz giris denemesi: 'admin'	127.0.0.1	2026-07-14 16:41:47.739728+03	\N
118	other	Basarisiz giris denemesi: 'admin'	127.0.0.1	2026-07-14 16:42:08.067876+03	\N
119	login	beril sisteme giris yapti.	127.0.0.1	2026-07-14 16:44:29.028127+03	1
120	logout	beril sistemden cikis yapti.	127.0.0.1	2026-07-14 16:45:04.149712+03	1
121	login	mustafa sisteme giris yapti.	127.0.0.1	2026-07-14 16:45:14.821399+03	2
122	logout	mustafa sistemden cikis yapti.	127.0.0.1	2026-07-14 16:45:17.557909+03	2
123	login	mustafa sisteme giris yapti.	127.0.0.1	2026-07-14 16:45:58.345465+03	2
124	logout	mustafa sistemden cikis yapti.	127.0.0.1	2026-07-14 16:47:08.568302+03	2
125	other	Basarisiz giris denemesi: 'beril'	127.0.0.1	2026-07-14 16:47:23.034796+03	\N
126	login	beril sisteme giris yapti.	127.0.0.1	2026-07-14 16:47:31.215275+03	1
127	logout	beril sistemden cikis yapti.	127.0.0.1	2026-07-14 16:50:06.027439+03	1
128	login	mustafa sisteme giris yapti.	127.0.0.1	2026-07-14 16:50:49.796279+03	2
129	logout	mustafa sistemden cikis yapti.	127.0.0.1	2026-07-14 16:51:16.034326+03	2
130	login	beril sisteme giris yapti.	127.0.0.1	2026-07-14 16:51:26.829718+03	1
131	logout	beril sistemden cikis yapti.	127.0.0.1	2026-07-14 16:55:24.742252+03	1
132	login	mustafa sisteme giris yapti.	127.0.0.1	2026-07-14 16:55:39.160713+03	2
133	logout	mustafa sistemden cikis yapti.	127.0.0.1	2026-07-14 16:55:58.386561+03	2
134	login	beril sisteme giris yapti.	127.0.0.1	2026-07-14 16:56:09.124725+03	1
135	login	beril sisteme giris yapti.	\N	2026-07-14 17:11:37.844005+03	1
136	login	beril sisteme giris yapti.	\N	2026-07-14 17:11:46.835292+03	1
137	logout	beril sistemden cikis yapti.	127.0.0.1	2026-07-14 17:29:47.101249+03	1
138	login	beril sisteme giris yapti.	127.0.0.1	2026-07-14 17:30:10.487613+03	1
139	logout	beril sistemden cikis yapti.	127.0.0.1	2026-07-14 17:30:20.420903+03	1
140	login	mustafa sisteme giris yapti.	127.0.0.1	2026-07-14 17:30:32.728934+03	2
141	logout	mustafa sistemden cikis yapti.	127.0.0.1	2026-07-15 10:28:59.792402+03	2
142	login	mustafa sisteme giris yapti.	127.0.0.1	2026-07-15 10:31:27.704265+03	2
143	logout	mustafa sistemden cikis yapti.	127.0.0.1	2026-07-15 10:32:16.775531+03	2
144	login	beril sisteme giris yapti.	127.0.0.1	2026-07-15 10:32:35.050958+03	1
145	logout	beril sistemden cikis yapti.	127.0.0.1	2026-07-16 08:24:15.641952+03	1
146	login	mustafa sisteme giris yapti.	127.0.0.1	2026-07-16 08:24:24.816737+03	2
147	logout	mustafa sistemden cikis yapti.	127.0.0.1	2026-07-16 08:24:47.156805+03	2
148	login	beril sisteme giris yapti.	127.0.0.1	2026-07-16 08:25:03.958336+03	1
149	other	Dell Sunucu X (ENV-0030) -> Can Korkmaz icin PDF zimmet tutanagi olusturuldu.	127.0.0.1	2026-07-16 08:26:18.722241+03	1
150	other	Apple Laptop S (ENV-0009) -> Elif Arslan icin PDF zimmet tutanagi olusturuldu.	127.0.0.1	2026-07-16 08:40:24.171403+03	1
151	other	Apple Laptop S (ENV-0009) -> Elif Arslan icin PDF zimmet tutanagi olusturuldu.	127.0.0.1	2026-07-16 08:54:03.762558+03	1
152	login	beril sisteme giris yapti.	\N	2026-07-16 09:01:57.604204+03	1
153	login	beril sisteme giris yapti.	\N	2026-07-16 09:02:04.604462+03	1
154	other	Apple Laptop S (ENV-0009) -> Elif Arslan icin PDF zimmet tutanagi olusturuldu.	127.0.0.1	2026-07-16 09:04:56.296823+03	1
155	other	Acer Diger Prime (ENV-0002) -> Fatma Çelik icin PDF zimmet tutanagi olusturuldu.	127.0.0.1	2026-07-16 09:07:32.815972+03	1
500	login	beril sisteme giris yapti.	\N	2026-07-16 09:42:56.989075+03	1
515	other	Acer Diger Prime (ENV-0002) -> Fatma Çelik icin PDF zimmet teslim tutanagi olusturuldu.	127.0.0.1	2026-07-16 09:56:58.92138+03	1
932	login	Beril Kahramanca sisteme giris yapti.	\N	2026-07-16 13:33:43.283865+03	1
968	other	Apple Laptop S -> Elif Arslan icin PDF zimmet teslim tutanagi olusturuldu.	127.0.0.1	2026-07-16 15:00:27.316847+03	1
969	other	Samsung Tablet 2024 -> Ahmet Şahin icin PDF zimmet teslim tutanagi olusturuldu.	127.0.0.1	2026-07-16 15:00:39.527985+03	1
975	logout	Beril Kahramanca sistemden cikis yapti.	127.0.0.1	2026-07-16 15:21:12.283632+03	1
976	login	Mustafa Yenidoğan sisteme giris yapti.	127.0.0.1	2026-07-16 15:21:21.504806+03	2
982	login	Beril Kahramanca sisteme giris yapti.	\N	2026-07-16 16:02:39.279762+03	1
992	login	Beril Kahramanca sisteme giris yapti.	\N	2026-07-16 16:31:55.588271+03	1
738	logout	Beril Kahramanca sistemden cikis yapti.	127.0.0.1	2026-07-16 11:57:11.724056+03	1
739	login	mustafa sisteme giris yapti.	127.0.0.1	2026-07-16 11:57:22.21776+03	2
1009	create	Calisan: 'Doğa Uslu' olusturuldu.	127.0.0.1	2026-07-16 16:40:34.600273+03	1
1010	update	Calisan: 'Doğa Uslu' guncellendi.	127.0.0.1	2026-07-16 16:40:34.756356+03	1
1011	create	Doğa Uslu icin otomatik kullanici hesabi olusturuldu (doga).	127.0.0.1	2026-07-16 16:40:34.757684+03	1
1012	logout	Beril Kahramanca sistemden cikis yapti.	127.0.0.1	2026-07-16 16:40:43.125182+03	1
1030	update	Calisan: 'Mustafa Yenidoğan' guncellendi.	127.0.0.1	2026-07-16 16:46:50.052418+03	1
1056	login	Beril Kahramanca sisteme giris yapti.	\N	2026-07-16 17:02:39.293123+03	1
1057	login	ahmet sisteme giris yapti.	\N	2026-07-16 17:02:39.400803+03	7
1075	logout	mustafa Doğan sistemden cikis yapti.	127.0.0.1	2026-07-16 17:10:46.099157+03	39
1076	login	Beril Kahramanca sisteme giris yapti.	127.0.0.1	2026-07-16 17:10:55.841842+03	1
1109	login	mustafa Doğan sisteme giris yapti.	127.0.0.1	2026-07-16 17:27:05.496757+03	39
1110	logout	mustafa Doğan sistemden cikis yapti.	127.0.0.1	2026-07-16 17:27:11.109382+03	39
1111	login	Beril Kahramanca sisteme giris yapti.	127.0.0.1	2026-07-16 17:27:26.707273+03	1
1121	return	Dell Sunucu X cihazi Can Korkmaz tarafindan iade edildi.	127.0.0.1	2026-07-16 19:27:40.674941+03	1
1122	other	Dell Sunucu X -> Can Korkmaz icin PDF iade teslim tutanagi olusturuldu.	127.0.0.1	2026-07-16 19:27:44.425259+03	1
1133	logout	Mustafa Yenidoğan sistemden cikis yapti.	127.0.0.1	2026-07-17 09:27:27.726669+03	2
1134	login	Beril Kahramanca sisteme giris yapti.	127.0.0.1	2026-07-17 09:27:49.669477+03	1
1135	other	Apple Laptop S -> Elif Arslan icin PDF zimmet teslim tutanagi olusturuldu.	127.0.0.1	2026-07-17 09:27:53.588648+03	1
696	delete	Cihaz: 'Apple Diger Air' silindi.	127.0.0.1	2026-07-16 11:24:45.78211+03	1
899	other	Apple Laptop S -> Elif Arslan icin PDF zimmet teslim tutanagi olusturuldu.	127.0.0.1	2026-07-16 13:20:59.955809+03	1
933	login	Beril Kahramanca sisteme giris yapti.	\N	2026-07-16 13:34:13.012244+03	1
740	logout	Mustafa Yenidoğan sistemden cikis yapti.	127.0.0.1	2026-07-16 11:57:53.612543+03	2
516	other	Acer Diger Prime (ENV-0002) -> Fatma Çelik icin PDF zimmet teslim tutanagi olusturuldu.	127.0.0.1	2026-07-16 10:08:22.473254+03	1
517	other	Apple Laptop S (ENV-0009) -> Elif Arslan icin PDF zimmet teslim tutanagi olusturuldu.	127.0.0.1	2026-07-16 10:08:34.772491+03	1
518	other	Apple Laptop S (ENV-0009) -> Elif Arslan icin PDF iade teslim tutanagi olusturuldu.	127.0.0.1	2026-07-16 10:08:40.743892+03	1
741	login	Beril Kahramanca sisteme giris yapti.	127.0.0.1	2026-07-16 11:58:14.417976+03	1
970	other	Samsung Tablet 2024 -> Ahmet Şahin icin PDF zimmet teslim tutanagi olusturuldu.	127.0.0.1	2026-07-16 15:01:35.546148+03	1
977	logout	Mustafa Yenidoğan sistemden cikis yapti.	127.0.0.1	2026-07-16 15:22:01.674453+03	2
978	login	Beril Kahramanca sisteme giris yapti.	127.0.0.1	2026-07-16 15:22:13.377287+03	1
983	login	Beril Kahramanca sisteme giris yapti.	\N	2026-07-16 16:30:38.914932+03	1
997	delete	Calisan: 'Ahmet Test' silindi.	\N	2026-07-16 16:32:38.030153+03	\N
998	delete	Calisan: 'Ahmet Test' silindi.	\N	2026-07-16 16:32:38.030914+03	\N
999	delete	Calisan: 'Özge Çelik' silindi.	\N	2026-07-16 16:32:38.031173+03	\N
1013	other	Basarisiz giris denemesi: 'doğa'	127.0.0.1	2026-07-16 16:40:52.041079+03	\N
1014	other	Basarisiz giris denemesi: 'Doğa'	127.0.0.1	2026-07-16 16:41:01.811688+03	\N
1015	other	Basarisiz giris denemesi: 'Doğa'	127.0.0.1	2026-07-16 16:41:10.60698+03	\N
1016	other	Basarisiz giris denemesi: 'Doğa'	127.0.0.1	2026-07-16 16:41:18.908492+03	\N
1017	other	Basarisiz giris denemesi: 'Doğa'	127.0.0.1	2026-07-16 16:41:23.428344+03	\N
1018	other	Basarisiz giris denemesi: 'doğa'	127.0.0.1	2026-07-16 16:41:31.998044+03	\N
1019	other	Basarisiz giris denemesi: 'doğa'	127.0.0.1	2026-07-16 16:41:35.204251+03	\N
1020	other	Basarisiz giris denemesi: 'Doğa'	127.0.0.1	2026-07-16 16:41:44.87285+03	\N
1031	create	Calisan: 'mustafaa aaa' olusturuldu.	127.0.0.1	2026-07-16 16:47:46.86928+03	1
1032	update	Calisan: 'mustafaa aaa' guncellendi.	127.0.0.1	2026-07-16 16:47:47.024278+03	1
1033	create	mustafaa aaa icin otomatik kullanici hesabi olusturuldu (mustafaa).	127.0.0.1	2026-07-16 16:47:47.02577+03	1
1034	logout	Beril Kahramanca sistemden cikis yapti.	127.0.0.1	2026-07-16 16:47:54.228363+03	1
1059	login	Beril Kahramanca sisteme giris yapti.	127.0.0.1	2026-07-16 17:05:42.060396+03	1
1060	delete	Calisan: 'Doğa Uslu' silindi.	127.0.0.1	2026-07-16 17:05:51.528524+03	1
1061	delete	Calisan: 'mustafa doğan' silindi.	127.0.0.1	2026-07-16 17:05:57.727009+03	1
1062	delete	Calisan: 'mustafaa aaa' silindi.	127.0.0.1	2026-07-16 17:06:00.444841+03	1
1077	create	Calisan: 'Doğa Uslu' olusturuldu.	127.0.0.1	2026-07-16 17:11:53.725355+03	1
1078	create	Doğa Uslu icin otomatik kullanici hesabi olusturuldu (doga@gmail.com).	127.0.0.1	2026-07-16 17:11:53.881263+03	1
1079	logout	Beril Kahramanca sistemden cikis yapti.	127.0.0.1	2026-07-16 17:11:57.27346+03	1
1080	login	Doğa Uslu sisteme giris yapti.	127.0.0.1	2026-07-16 17:12:08.844374+03	40
1035	login	mustafaa aaa sisteme giris yapti.	127.0.0.1	2026-07-16 16:48:07.198036+03	\N
1058	logout	mustafaa aaa sistemden cikis yapti.	127.0.0.1	2026-07-16 17:05:32.70102+03	\N
1112	create	Calisan: 'hüsnü hüsnü' olusturuldu.	127.0.0.1	2026-07-16 17:29:34.631609+03	1
1113	create	hüsnü hüsnü icin otomatik kullanici hesabi olusturuldu (husnu@gmail.com).	127.0.0.1	2026-07-16 17:29:34.788268+03	1
1114	logout	Beril Kahramanca sistemden cikis yapti.	127.0.0.1	2026-07-16 17:29:38.454168+03	1
1115	login	hüsnü hüsnü sisteme giris yapti.	127.0.0.1	2026-07-16 17:29:52.134337+03	42
1123	login	Beril Kahramanca sisteme giris yapti.	\N	2026-07-17 08:14:36.943994+03	1
1124	login	ahmet sisteme giris yapti.	\N	2026-07-17 08:14:37.071021+03	7
1136	login	Beril Kahramanca sisteme giris yapti.	\N	2026-07-17 09:54:46.076402+03	1
509	other	Cihaz listesi Excel olarak disa aktarildi.	127.0.0.1	2026-07-16 09:45:26.011991+03	1
519	other	Acer Diger Prime (ENV-0002) -> Fatma Çelik icin PDF zimmet teslim tutanagi olusturuldu.	127.0.0.1	2026-07-16 10:33:55.280628+03	1
697	delete	Cihaz: 'Huawei Telefon S' silindi.	127.0.0.1	2026-07-16 11:25:00.381404+03	1
698	delete	Cihaz: 'Acer Telefon Lite' silindi.	127.0.0.1	2026-07-16 11:25:05.682347+03	1
699	update	Cihaz: 'Acer Diger X' guncellendi.	127.0.0.1	2026-07-16 11:25:24.449732+03	1
700	delete	Cihaz: 'Asus Sunucu 2024' silindi.	127.0.0.1	2026-07-16 11:25:32.463372+03	1
934	login	Beril Kahramanca sisteme giris yapti.	\N	2026-07-16 13:38:47.797899+03	1
960	other	Apple Laptop S -> Elif Arslan icin PDF zimmet teslim tutanagi olusturuldu.	127.0.0.1	2026-07-16 13:57:11.699555+03	1
961	other	Apple Laptop S -> Elif Arslan icin PDF iade teslim tutanagi olusturuldu.	127.0.0.1	2026-07-16 13:57:18.772762+03	1
962	other	Acer Diger Prime -> Fatma Çelik icin PDF zimmet teslim tutanagi olusturuldu.	127.0.0.1	2026-07-16 13:57:22.691071+03	1
963	other	Acer Diger Prime -> Fatma Çelik icin PDF iade teslim tutanagi olusturuldu.	127.0.0.1	2026-07-16 13:57:26.794904+03	1
964	return	Samsung Tablet Elite cihazi Ayşe Demir tarafindan iade edildi.	127.0.0.1	2026-07-16 13:57:42.030658+03	1
965	other	Samsung Tablet Elite -> Ayşe Demir icin PDF zimmet teslim tutanagi olusturuldu.	127.0.0.1	2026-07-16 13:57:44.042265+03	1
971	return	Samsung Tablet 2024 cihazi Ahmet Şahin tarafindan iade edildi.	127.0.0.1	2026-07-16 15:07:41.504407+03	1
972	other	Samsung Tablet 2024 -> Ahmet Şahin icin PDF iade teslim tutanagi olusturuldu.	127.0.0.1	2026-07-16 15:07:43.773757+03	1
979	login	Beril Kahramanca sisteme giris yapti.	\N	2026-07-16 15:47:56.427625+03	1
989	login	ahmet sisteme giris yapti.	\N	2026-07-16 16:31:00.502473+03	7
1000	login	Beril Kahramanca sisteme giris yapti.	\N	2026-07-16 16:34:12.826036+03	1
1001	login	ahmet sisteme giris yapti.	\N	2026-07-16 16:34:12.919685+03	7
1021	other	Basarisiz giris denemesi: 'Beril'	127.0.0.1	2026-07-16 16:41:55.938164+03	\N
1022	login	Beril Kahramanca sisteme giris yapti.	127.0.0.1	2026-07-16 16:42:01.984386+03	1
1023	create	Calisan: 'mustafa doğan' olusturuldu.	127.0.0.1	2026-07-16 16:42:53.133476+03	1
1024	update	Calisan: 'mustafa doğan' guncellendi.	127.0.0.1	2026-07-16 16:42:53.289903+03	1
1025	create	mustafa doğan icin otomatik kullanici hesabi olusturuldu (mustafa2).	127.0.0.1	2026-07-16 16:42:53.291418+03	1
1036	login	ahmet sisteme giris yapti.	\N	2026-07-16 16:52:08.213122+03	7
1063	create	Calisan: 'mustafa Doğan' olusturuldu.	127.0.0.1	2026-07-16 17:06:49.279296+03	1
1064	create	mustafa Doğan icin otomatik kullanici hesabi olusturuldu (mustafa1@gmail.com).	127.0.0.1	2026-07-16 17:06:49.43543+03	1
1065	logout	Beril Kahramanca sistemden cikis yapti.	127.0.0.1	2026-07-16 17:06:55.473519+03	1
1066	other	Basarisiz giris denemesi: 'mustafa'	127.0.0.1	2026-07-16 17:07:05.708627+03	\N
1067	login	mustafa Doğan sisteme giris yapti.	127.0.0.1	2026-07-16 17:07:20.852849+03	39
1081	other	Basarisiz giris denemesi: 'ayse@gmail.com'	\N	2026-07-16 17:22:28.807975+03	\N
1082	other	Basarisiz giris denemesi: 'ayşe'	\N	2026-07-16 17:22:28.956538+03	\N
1083	other	Basarisiz giris denemesi: 'mehmet@gmail.com'	\N	2026-07-16 17:22:29.102981+03	\N
1084	other	Basarisiz giris denemesi: 'mehmet'	\N	2026-07-16 17:22:29.248356+03	\N
1085	other	Basarisiz giris denemesi: 'fatma@gmail.com'	\N	2026-07-16 17:22:29.393731+03	\N
1086	other	Basarisiz giris denemesi: 'fatma'	\N	2026-07-16 17:22:29.539325+03	\N
1087	other	Basarisiz giris denemesi: 'ahmet@gmail.com'	\N	2026-07-16 17:22:29.686017+03	\N
1088	other	Basarisiz giris denemesi: 'ahmet'	\N	2026-07-16 17:22:29.832132+03	\N
1089	other	Basarisiz giris denemesi: 'elif@gmail.com'	\N	2026-07-16 17:22:29.977234+03	\N
1090	other	Basarisiz giris denemesi: 'elif'	\N	2026-07-16 17:22:30.123577+03	\N
1091	other	Basarisiz giris denemesi: 'can@gmail.com'	\N	2026-07-16 17:22:30.267116+03	\N
1092	other	Basarisiz giris denemesi: 'can'	\N	2026-07-16 17:22:30.411183+03	\N
1093	other	Basarisiz giris denemesi: 'emre@gmail.com'	\N	2026-07-16 17:22:30.554097+03	\N
1094	other	Basarisiz giris denemesi: 'emre'	\N	2026-07-16 17:22:30.69854+03	\N
1095	other	Basarisiz giris denemesi: 'mustafa@gmail.com'	\N	2026-07-16 17:22:30.84169+03	\N
1096	other	Basarisiz giris denemesi: 'mustafa'	\N	2026-07-16 17:22:30.986235+03	\N
1097	other	Basarisiz giris denemesi: 'fatih@gmail.com'	\N	2026-07-16 17:22:31.131665+03	\N
1098	other	Basarisiz giris denemesi: 'fatih'	\N	2026-07-16 17:22:31.275898+03	\N
1099	other	Basarisiz giris denemesi: 'mustafa1@gmail.com'	\N	2026-07-16 17:22:31.418836+03	\N
1100	other	Basarisiz giris denemesi: 'mustafa1@gmail.com'	\N	2026-07-16 17:22:31.56448+03	\N
1101	other	Basarisiz giris denemesi: 'doga@gmail.com'	\N	2026-07-16 17:22:31.708101+03	\N
1102	other	Basarisiz giris denemesi: 'doga@gmail.com'	\N	2026-07-16 17:22:31.850844+03	\N
1116	logout	hüsnü hüsnü sistemden cikis yapti.	127.0.0.1	2026-07-16 17:31:25.23777+03	42
1125	login	Beril Kahramanca sisteme giris yapti.	\N	2026-07-17 08:15:01.283041+03	1
1126	login	ahmet sisteme giris yapti.	\N	2026-07-17 08:15:01.385656+03	7
510	other	Apple Laptop S (ENV-0009) -> Elif Arslan icin PDF zimmet teslim tutanagi olusturuldu.	127.0.0.1	2026-07-16 09:45:42.878603+03	1
520	update	Cihaz: 'Acer Diger Prime (ENV-0002)' guncellendi.	127.0.0.1	2026-07-16 10:37:06.417799+03	1
521	return	Acer Diger Prime (ENV-0002) cihazi Fatma Çelik tarafindan iade edildi.	127.0.0.1	2026-07-16 10:37:06.436005+03	1
522	other	Acer Diger Prime (ENV-0002) -> Fatma Çelik icin PDF iade teslim tutanagi olusturuldu.	127.0.0.1	2026-07-16 10:37:12.321108+03	1
701	other	Acer Diger Prime -> Fatma Çelik icin PDF iade teslim tutanagi olusturuldu.	127.0.0.1	2026-07-16 11:26:20.955275+03	1
702	other	Acer Diger Prime -> Fatma Çelik icin PDF zimmet teslim tutanagi olusturuldu.	127.0.0.1	2026-07-16 11:26:24.365327+03	1
734	other	Acer Diger Prime -> Fatma Çelik icin PDF zimmet teslim tutanagi olusturuldu.	127.0.0.1	2026-07-16 11:49:07.486605+03	1
735	other	Acer Diger Prime -> Fatma Çelik icin PDF iade teslim tutanagi olusturuldu.	127.0.0.1	2026-07-16 11:49:26.028076+03	1
747	login	Beril Kahramanca sisteme giris yapti.	\N	2026-07-16 13:10:58.932932+03	1
935	login	Beril Kahramanca sisteme giris yapti.	\N	2026-07-16 13:39:48.759554+03	1
966	other	Apple Laptop S -> Elif Arslan icin PDF zimmet teslim tutanagi olusturuldu.	127.0.0.1	2026-07-16 14:53:03.987224+03	1
973	login	Beril Kahramanca sisteme giris yapti.	\N	2026-07-16 15:20:22.150819+03	1
980	login	Beril Kahramanca sisteme giris yapti.	\N	2026-07-16 15:57:50.497947+03	1
990	login	ahmet sisteme giris yapti.	\N	2026-07-16 16:31:20.309835+03	7
1002	create	Calisan: 'Fatih Üret' olusturuldu.	127.0.0.1	2026-07-16 16:36:38.098831+03	1
1003	update	Calisan: 'Fatih Üret' guncellendi.	127.0.0.1	2026-07-16 16:36:38.245572+03	1
1004	create	Fatih Üret icin otomatik kullanici hesabi olusturuldu (fatih).	127.0.0.1	2026-07-16 16:36:38.247179+03	1
1005	logout	Beril Kahramanca sistemden cikis yapti.	127.0.0.1	2026-07-16 16:36:44.630662+03	1
1006	login	Fatih Üret sisteme giris yapti.	127.0.0.1	2026-07-16 16:36:54.765875+03	35
1026	logout	Beril Kahramanca sistemden cikis yapti.	127.0.0.1	2026-07-16 16:42:58.758254+03	1
1037	other	Basarisiz giris denemesi: 'ayşe'	\N	2026-07-16 17:01:42.468049+03	\N
1038	other	Basarisiz giris denemesi: 'ayse@gmail.com'	\N	2026-07-16 17:01:42.756963+03	\N
1039	other	Basarisiz giris denemesi: 'mehmet'	\N	2026-07-16 17:01:43.042962+03	\N
1040	other	Basarisiz giris denemesi: 'mehmet@gmail.com'	\N	2026-07-16 17:01:43.326676+03	\N
1041	other	Basarisiz giris denemesi: 'fatma'	\N	2026-07-16 17:01:43.612348+03	\N
1042	other	Basarisiz giris denemesi: 'fatma@gmail.com'	\N	2026-07-16 17:01:43.899318+03	\N
1043	other	Basarisiz giris denemesi: 'ahmet'	\N	2026-07-16 17:01:44.186738+03	\N
1044	other	Basarisiz giris denemesi: 'ahmet@gmail.com'	\N	2026-07-16 17:01:44.474019+03	\N
1045	other	Basarisiz giris denemesi: 'elif'	\N	2026-07-16 17:01:44.760006+03	\N
1046	other	Basarisiz giris denemesi: 'elif@gmail.com'	\N	2026-07-16 17:01:45.047449+03	\N
1047	other	Basarisiz giris denemesi: 'can'	\N	2026-07-16 17:01:45.334484+03	\N
1048	other	Basarisiz giris denemesi: 'can@gmail.com'	\N	2026-07-16 17:01:45.620525+03	\N
1049	other	Basarisiz giris denemesi: 'emre'	\N	2026-07-16 17:01:45.90716+03	\N
1050	other	Basarisiz giris denemesi: 'emre@gmail.com'	\N	2026-07-16 17:01:46.19356+03	\N
1051	other	Basarisiz giris denemesi: 'mustafa'	\N	2026-07-16 17:01:46.486675+03	\N
1052	other	Basarisiz giris denemesi: 'mustafa@gmail.com'	\N	2026-07-16 17:01:46.772578+03	\N
1053	other	Basarisiz giris denemesi: 'fatih'	\N	2026-07-16 17:01:47.059948+03	\N
1054	other	Basarisiz giris denemesi: 'fatih@gmail.com'	\N	2026-07-16 17:01:47.347707+03	\N
1068	logout	mustafa Doğan sistemden cikis yapti.	127.0.0.1	2026-07-16 17:08:52.949366+03	39
1027	login	mustafa doğan sisteme giris yapti.	127.0.0.1	2026-07-16 16:43:09.683119+03	\N
1103	login	Beril Kahramanca sisteme giris yapti.	127.0.0.1	2026-07-16 17:25:12.141916+03	1
1117	login	Beril Kahramanca sisteme giris yapti.	127.0.0.1	2026-07-16 17:31:42.646165+03	1
1127	other	HP Sunucu 2024 -> Mustafa Yenidoğan icin PDF zimmet teslim tutanagi olusturuldu.	127.0.0.1	2026-07-17 09:26:00.493808+03	1
511	update	Cihaz: 'Apple Laptop S (ENV-0009)' guncellendi.	127.0.0.1	2026-07-16 09:46:58.740707+03	1
512	return	Apple Laptop S (ENV-0009) cihazi Elif Arslan tarafindan iade edildi.	127.0.0.1	2026-07-16 09:46:58.908862+03	1
513	other	Apple Laptop S (ENV-0009) -> Elif Arslan icin PDF zimmet teslim tutanagi olusturuldu.	127.0.0.1	2026-07-16 09:47:02.355298+03	1
514	other	Apple Laptop S (ENV-0009) -> Elif Arslan icin PDF iade teslim tutanagi olusturuldu.	127.0.0.1	2026-07-16 09:47:05.989216+03	1
736	assign	HP Yazici Max cihazi Emre Aydın adli calisana zimmetlendi.	127.0.0.1	2026-07-16 11:50:27.368961+03	1
737	other	HP Yazici Max -> Emre Aydın icin PDF zimmet teslim tutanagi olusturuldu.	127.0.0.1	2026-07-16 11:50:31.48063+03	1
967	other	Apple Laptop S -> Elif Arslan icin PDF iade teslim tutanagi olusturuldu.	127.0.0.1	2026-07-16 14:53:50.629723+03	1
974	login	Beril Kahramanca sisteme giris yapti.	\N	2026-07-16 15:20:28.751533+03	1
981	login	Beril Kahramanca sisteme giris yapti.	\N	2026-07-16 16:00:56.22379+03	1
991	login	ahmet sisteme giris yapti.	\N	2026-07-16 16:31:35.222858+03	7
1007	logout	Fatih Üret sistemden cikis yapti.	127.0.0.1	2026-07-16 16:37:46.528689+03	35
1008	login	Beril Kahramanca sisteme giris yapti.	127.0.0.1	2026-07-16 16:38:01.879399+03	1
1029	login	Beril Kahramanca sisteme giris yapti.	127.0.0.1	2026-07-16 16:46:11.20189+03	1
1055	login	ahmet sisteme giris yapti.	\N	2026-07-16 17:02:12.445289+03	7
1069	other	Basarisiz giris denemesi: 'mustafa Doğan'	127.0.0.1	2026-07-16 17:09:04.235254+03	\N
1070	other	Basarisiz giris denemesi: 'mustafa Doğan'	127.0.0.1	2026-07-16 17:09:08.936462+03	\N
1071	other	Basarisiz giris denemesi: 'mustafa'	127.0.0.1	2026-07-16 17:09:20.86561+03	\N
1072	other	Basarisiz giris denemesi: 'mustafa'	127.0.0.1	2026-07-16 17:09:24.733526+03	\N
1073	other	Basarisiz giris denemesi: 'mustafa1@gmail.com'	127.0.0.1	2026-07-16 17:09:34.835497+03	\N
1074	login	mustafa Doğan sisteme giris yapti.	127.0.0.1	2026-07-16 17:09:39.340495+03	39
499	login	beril sisteme giris yapti.	\N	2026-07-16 09:42:18.437648+03	1
1028	logout	mustafa doğan sistemden cikis yapti.	127.0.0.1	2026-07-16 16:45:57.697292+03	\N
1104	create	Calisan: 'hasan kaynak' olusturuldu.	127.0.0.1	2026-07-16 17:26:16.47383+03	1
1105	create	hasan kaynak icin otomatik kullanici hesabi olusturuldu (hasan@gmail.com).	127.0.0.1	2026-07-16 17:26:16.634525+03	1
1106	logout	Beril Kahramanca sistemden cikis yapti.	127.0.0.1	2026-07-16 17:26:20.877955+03	1
1107	login	hasan kaynak sisteme giris yapti.	127.0.0.1	2026-07-16 17:26:32.552425+03	41
1108	logout	hasan kaynak sistemden cikis yapti.	127.0.0.1	2026-07-16 17:26:52.651383+03	41
1118	other	Dell Sunucu X -> Can Korkmaz icin PDF zimmet teslim tutanagi olusturuldu.	127.0.0.1	2026-07-16 19:24:53.91392+03	1
1119	other	Acer Diger Prime -> Fatma Çelik icin PDF zimmet teslim tutanagi olusturuldu.	127.0.0.1	2026-07-16 19:25:18.210027+03	1
1120	other	Apple Laptop S -> Elif Arslan icin PDF zimmet teslim tutanagi olusturuldu.	127.0.0.1	2026-07-16 19:25:24.963341+03	1
1128	other	Acer Diger Prime -> Fatma Çelik icin PDF zimmet teslim tutanagi olusturuldu.	127.0.0.1	2026-07-17 09:26:13.511578+03	1
1129	return	HP Sunucu 2024 cihazi Mustafa Yenidoğan tarafindan iade edildi.	127.0.0.1	2026-07-17 09:26:27.857943+03	1
1130	other	HP Sunucu 2024 -> Mustafa Yenidoğan icin PDF iade teslim tutanagi olusturuldu.	127.0.0.1	2026-07-17 09:26:30.857999+03	1
1131	logout	Beril Kahramanca sistemden cikis yapti.	127.0.0.1	2026-07-17 09:26:48.618884+03	1
1132	login	Mustafa Yenidoğan sisteme giris yapti.	127.0.0.1	2026-07-17 09:27:03.796947+03	2
\.


--
-- Data for Name: inventory_assignment; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.inventory_assignment (id, created_at, updated_at, assigned_date, expected_return_date, returned_date, notes, return_notes, returned, assigned_by_id, returned_by_id, device_id, employee_id, return_condition, damage_description) FROM stdin;
1	2026-07-14 16:39:34.360299+03	2026-07-14 16:39:34.360303+03	2025-12-28	2026-12-28	\N	Ornek zimmet.		f	1	\N	39	3		
2	2026-07-14 16:39:34.374648+03	2026-07-14 16:39:34.37465+03	2026-03-09	2027-03-09	\N	Ornek zimmet.		f	1	\N	5	6		
3	2026-07-14 16:39:34.383282+03	2026-07-14 16:39:34.383284+03	2026-05-21	2027-05-21	\N	Ornek zimmet.		f	1	\N	37	6		
4	2026-07-14 16:39:34.392361+03	2026-07-14 16:39:34.392364+03	2025-10-07	2026-10-07	\N	Ornek zimmet.		f	1	\N	11	8		
102	2026-07-16 11:50:27.368184+03	2026-07-16 11:50:27.368199+03	2026-07-16	\N	\N			f	1	\N	3	7		
8	2026-07-14 16:39:34.429429+03	2026-07-14 16:39:34.429431+03	2025-10-17	2026-10-17	\N	Ornek zimmet.		f	1	\N	10	4		
9	2026-07-14 16:39:34.438981+03	2026-07-14 16:39:34.438984+03	2025-12-21	2026-12-21	\N	Ornek zimmet.		f	1	\N	12	3		
12	2026-07-14 16:39:34.467326+03	2026-07-14 16:39:34.467329+03	2025-10-11	2026-10-11	\N	Ornek zimmet.		f	1	\N	32	8		
13	2026-07-14 16:39:34.476502+03	2026-07-14 16:39:34.476504+03	2025-10-12	2026-10-12	\N	Ornek zimmet.		f	1	\N	17	5		
15	2026-07-14 16:39:34.494866+03	2026-07-14 16:39:34.494869+03	2025-09-21	2026-09-21	\N	Ornek zimmet.		f	1	\N	14	5		
14	2026-07-14 16:39:34.485989+03	2026-07-16 13:57:42.028236+03	2026-04-17	2027-04-17	2026-07-16	Ornek zimmet.		t	1	1	7	1	undamaged	
5	2026-07-14 16:39:34.401596+03	2026-07-16 15:07:41.50143+03	2026-07-05	2027-07-05	2026-07-16	Ornek zimmet.		t	1	1	21	4	undamaged	
11	2026-07-14 16:39:34.457802+03	2026-07-16 19:27:40.672867+03	2026-06-16	2027-06-16	2026-07-16	Ornek zimmet.		t	1	1	14	6	undamaged	
6	2026-07-14 16:39:34.411285+03	2026-07-17 09:26:27.856121+03	2026-05-31	2027-05-31	2026-07-17	Ornek zimmet.		t	1	1	13	8	damaged	kırık getirdi
10	2026-07-14 16:39:34.448635+03	2026-07-16 09:46:58.738026+03	2026-07-10	2027-07-10	2026-07-16	Ornek zimmet.		t	1	1	9	5	undamaged	
7	2026-07-14 16:39:34.421069+03	2026-07-16 10:37:06.414921+03	2026-07-09	2027-07-09	2026-07-16	Ornek zimmet.		t	1	1	2	3	undamaged	
\.


--
-- Data for Name: inventory_company; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.inventory_company (id, created_at, updated_at, name) FROM stdin;
1	2026-07-16 11:15:15.285161+03	2026-07-16 11:15:15.285171+03	Craniocatch
2	2026-07-16 11:15:15.286023+03	2026-07-16 11:15:15.286026+03	Engelsiz Ceviri
3	2026-07-16 11:15:15.286565+03	2026-07-16 11:15:15.286568+03	Nevisoft
\.


--
-- Data for Name: inventory_device; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.inventory_device (id, created_at, updated_at, name, total_quantity) FROM stdin;
1	2026-07-14 16:39:32.718709+03	2026-07-14 16:39:32.718713+03	Lenovo Monitor Plus	1
2	2026-07-14 16:39:34.095666+03	2026-07-16 10:37:06.41641+03	Acer Diger Prime	1
5	2026-07-14 16:39:34.122026+03	2026-07-14 16:39:34.374924+03	Dell Sunucu Pro	1
12	2026-07-14 16:39:34.174424+03	2026-07-14 16:39:34.439329+03	HP Sunucu Lite	1
34	2026-07-14 16:39:34.313936+03	2026-07-14 16:39:34.313938+03	Lenovo Diger S	1
35	2026-07-14 16:39:34.319477+03	2026-07-14 16:39:34.319479+03	Asus Laptop Elite	1
36	2026-07-14 16:39:34.325191+03	2026-07-14 16:39:34.325194+03	HP Telefon X	1
37	2026-07-14 16:39:34.330604+03	2026-07-14 16:39:34.383469+03	HP Diger Prime	1
38	2026-07-14 16:39:34.335955+03	2026-07-14 16:39:34.335957+03	HP Diger Max	1
39	2026-07-14 16:39:34.342658+03	2026-07-14 16:39:34.363165+03	Lenovo Diger Lite	1
40	2026-07-14 16:39:34.348431+03	2026-07-14 16:39:34.348433+03	Apple Laptop Air	1
3	2026-07-14 16:39:34.106809+03	2026-07-14 16:39:34.106812+03	HP Yazici Max	1
4	2026-07-14 16:39:34.113983+03	2026-07-14 16:39:34.113986+03	Lenovo Sunucu Max	1
6	2026-07-14 16:39:34.129691+03	2026-07-14 16:39:34.129694+03	Lenovo Yazici 2024	1
7	2026-07-14 16:39:34.137371+03	2026-07-14 16:39:34.486364+03	Samsung Tablet Elite	1
8	2026-07-14 16:39:34.144753+03	2026-07-14 16:39:34.144758+03	Apple Sunucu Pro	1
9	2026-07-14 16:39:34.152017+03	2026-07-16 09:46:58.739408+03	Apple Laptop S	1
10	2026-07-14 16:39:34.159274+03	2026-07-14 16:39:34.429701+03	Acer Telefon Pro	1
11	2026-07-14 16:39:34.167064+03	2026-07-14 16:39:34.392586+03	Samsung Yazici Max	1
13	2026-07-14 16:39:34.181778+03	2026-07-14 16:39:34.411564+03	HP Sunucu 2024	1
14	2026-07-14 16:39:34.189273+03	2026-07-14 16:39:34.495129+03	Dell Sunucu X	2
16	2026-07-14 16:39:34.20356+03	2026-07-14 16:39:34.203562+03	Acer Yazici Pro	1
17	2026-07-14 16:39:34.210397+03	2026-07-14 16:39:34.476773+03	Asus Laptop S	1
18	2026-07-14 16:39:34.217213+03	2026-07-14 16:39:34.217216+03	Asus Diger Plus	1
19	2026-07-14 16:39:34.224686+03	2026-07-14 16:39:34.22469+03	Apple Tablet 2024	1
20	2026-07-14 16:39:34.231216+03	2026-07-14 16:39:34.231219+03	Dell Diger Pro	1
21	2026-07-14 16:39:34.2374+03	2026-07-14 16:39:34.401807+03	Samsung Tablet 2024	1
23	2026-07-14 16:39:34.250269+03	2026-07-14 16:39:34.250272+03	Huawei Telefon Lite	1
25	2026-07-14 16:39:34.262168+03	2026-07-14 16:39:34.26217+03	Dell Sunucu Elite	1
26	2026-07-14 16:39:34.267991+03	2026-07-14 16:39:34.267994+03	Apple Sunucu X	1
27	2026-07-14 16:39:34.273801+03	2026-07-14 16:39:34.273807+03	Asus Laptop X	1
29	2026-07-14 16:39:34.285043+03	2026-07-14 16:39:34.285045+03	Dell Monitor 2024	1
31	2026-07-14 16:39:34.296328+03	2026-07-14 16:39:34.29633+03	Acer Yazici Lite	1
32	2026-07-14 16:39:34.301918+03	2026-07-14 16:39:34.467706+03	Lenovo Yazici X	1
28	2026-07-14 16:39:34.279264+03	2026-07-16 11:25:24.448658+03	Acer Diger X	4
\.


--
-- Data for Name: inventory_employee; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.inventory_employee (id, created_at, updated_at, first_name, last_name, email, profile_photo, is_active, user_id, tc_kimlik_no, hire_date, company_id) FROM stdin;
111	2026-07-16 17:06:49.278469+03	2026-07-16 17:06:49.278485+03	mustafa	Doğan	mustafa1@gmail.com		t	39	11111111111	2026-03-21	1
112	2026-07-16 17:11:53.724567+03	2026-07-16 17:11:53.724583+03	Doğa	Uslu	doga@gmail.com		t	40	87983475934	2026-03-04	3
113	2026-07-16 17:26:16.472857+03	2026-07-16 17:26:16.472873+03	hasan	kaynak	hasan@gmail.com		t	41	72873682763	2892-09-08	1
114	2026-07-16 17:29:34.630938+03	2026-07-16 17:29:34.630951+03	hüsnü	hüsnü	husnu@gmail.com		t	42	74846735946	2006-05-06	3
1	2026-07-14 15:47:19.603311+03	2026-07-14 15:47:19.60334+03	Ayşe	Demir	ayse@gmail.com		t	4	90000000001	2026-07-14	1
2	2026-07-14 15:47:46.034271+03	2026-07-14 15:47:46.034299+03	Mehmet	Kaya	mehmet@gmail.com		t	5	90000000002	2026-07-14	2
3	2026-07-14 15:48:15.536021+03	2026-07-14 15:48:15.536045+03	Fatma	Çelik	fatma@gmail.com		t	6	90000000003	2026-07-14	3
4	2026-07-14 15:48:50.651529+03	2026-07-14 15:48:50.651554+03	Ahmet	Şahin	ahmet@gmail.com		t	7	90000000004	2026-07-14	1
5	2026-07-14 15:49:17.122845+03	2026-07-14 15:49:17.122873+03	Elif	Arslan	elif@gmail.com		t	8	90000000005	2026-07-14	2
6	2026-07-14 15:49:49.947986+03	2026-07-14 15:49:49.948015+03	Can	Korkmaz	can@gmail.com		t	9	90000000006	2026-07-14	3
7	2026-07-14 15:50:21.754524+03	2026-07-14 15:50:21.754551+03	Emre	Aydın	emre@gmail.com		t	10	90000000007	2026-07-14	1
107	2026-07-16 16:36:38.098028+03	2026-07-16 16:36:38.098043+03	Fatih	Üret	fatih@gmail.com		t	35	90000000012	2026-07-16	2
8	2026-07-14 15:51:56.424536+03	2026-07-16 16:46:50.051469+03	Mustafa	Yenidoğan	mustafa@gmail.com		f	2	90000000008	2026-07-14	2
\.


--
-- Data for Name: inventory_notification; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.inventory_notification (id, title, message, link, is_read, created_at, user_id) FROM stdin;
1	Yeni Zimmet Olusturuldu	Lenovo Diger Lite (ENV-0039) cihazi uzerinize zimmetlendi.	/envanter/cihazlar/39/	f	2026-07-14 16:39:34.369657+03	6
2	Yeni Zimmet Olusturuldu	Dell Sunucu Pro (ENV-0005) cihazi uzerinize zimmetlendi.	/envanter/cihazlar/5/	f	2026-07-14 16:39:34.380068+03	9
3	Yeni Zimmet Olusturuldu	HP Diger Prime (ENV-0037) cihazi uzerinize zimmetlendi.	/envanter/cihazlar/37/	f	2026-07-14 16:39:34.389259+03	9
4	Yeni Zimmet Olusturuldu	Samsung Yazici Max (ENV-0011) cihazi uzerinize zimmetlendi.	/envanter/cihazlar/11/	f	2026-07-14 16:39:34.398398+03	2
5	Yeni Zimmet Olusturuldu	Samsung Tablet 2024 (ENV-0021) cihazi uzerinize zimmetlendi.	/envanter/cihazlar/21/	f	2026-07-14 16:39:34.407804+03	7
6	Yeni Zimmet Olusturuldu	HP Sunucu 2024 (ENV-0013) cihazi uzerinize zimmetlendi.	/envanter/cihazlar/13/	f	2026-07-14 16:39:34.417372+03	2
7	Yeni Zimmet Olusturuldu	Acer Diger Prime (ENV-0002) cihazi uzerinize zimmetlendi.	/envanter/cihazlar/2/	f	2026-07-14 16:39:34.426712+03	6
8	Yeni Zimmet Olusturuldu	Acer Telefon Pro (ENV-0010) cihazi uzerinize zimmetlendi.	/envanter/cihazlar/10/	f	2026-07-14 16:39:34.435738+03	7
9	Yeni Zimmet Olusturuldu	HP Sunucu Lite (ENV-0012) cihazi uzerinize zimmetlendi.	/envanter/cihazlar/12/	f	2026-07-14 16:39:34.445512+03	6
10	Yeni Zimmet Olusturuldu	Apple Laptop S (ENV-0009) cihazi uzerinize zimmetlendi.	/envanter/cihazlar/9/	f	2026-07-14 16:39:34.454621+03	8
11	Yeni Zimmet Olusturuldu	Dell Sunucu X (ENV-0030) cihazi uzerinize zimmetlendi.	/envanter/cihazlar/30/	f	2026-07-14 16:39:34.463804+03	9
12	Yeni Zimmet Olusturuldu	Lenovo Yazici X (ENV-0032) cihazi uzerinize zimmetlendi.	/envanter/cihazlar/32/	f	2026-07-14 16:39:34.4736+03	2
13	Yeni Zimmet Olusturuldu	Asus Laptop S (ENV-0017) cihazi uzerinize zimmetlendi.	/envanter/cihazlar/17/	f	2026-07-14 16:39:34.482684+03	8
14	Yeni Zimmet Olusturuldu	Samsung Tablet Elite (ENV-0007) cihazi uzerinize zimmetlendi.	/envanter/cihazlar/7/	f	2026-07-14 16:39:34.492039+03	4
15	Yeni Zimmet Olusturuldu	Dell Sunucu X (ENV-0014) cihazi uzerinize zimmetlendi.	/envanter/cihazlar/14/	f	2026-07-14 16:39:34.500904+03	8
28	Cihaz Iadesi Alindi	Apple Laptop S (ENV-0009) cihazinin iadesi basariyla alindi.	/envanter/cihazlar/9/	f	2026-07-16 09:46:58.909637+03	8
29	Cihaz Iadesi Alindi	Acer Diger Prime (ENV-0002) cihazinin iadesi basariyla alindi.	/envanter/cihazlar/2/	f	2026-07-16 10:37:06.436936+03	6
168	Cihaz Iadesi Alindi	Samsung Tablet Elite cihazinin iadesi basariyla alindi.	/envanter/cihazlarim/	f	2026-07-16 13:57:42.032133+03	4
169	Cihaz Iadesi Alindi	Samsung Tablet 2024 cihazinin iadesi basariyla alindi.	/envanter/cihazlarim/	f	2026-07-16 15:07:41.505955+03	7
171	Yeni Personel Eklendi	Fatih Üret sisteme yeni calisan olarak eklendi.	/envanter/calisanlar/107/	t	2026-07-16 16:36:38.246706+03	1
172	Yeni Personel Eklendi	Doğa Uslu sisteme yeni calisan olarak eklendi.	/envanter/calisanlar/108/	f	2026-07-16 16:40:34.75721+03	1
173	Yeni Personel Eklendi	mustafa doğan sisteme yeni calisan olarak eklendi.	/envanter/calisanlar/109/	f	2026-07-16 16:42:53.290936+03	1
174	Yeni Personel Eklendi	mustafaa aaa sisteme yeni calisan olarak eklendi.	/envanter/calisanlar/110/	f	2026-07-16 16:47:47.025316+03	1
175	Yeni Personel Eklendi	mustafa Doğan sisteme yeni calisan olarak eklendi.	/envanter/calisanlar/111/	f	2026-07-16 17:06:49.434359+03	1
176	Yeni Personel Eklendi	Doğa Uslu sisteme yeni calisan olarak eklendi.	/envanter/calisanlar/112/	f	2026-07-16 17:11:53.880482+03	1
177	Yeni Personel Eklendi	hasan kaynak sisteme yeni calisan olarak eklendi.	/envanter/calisanlar/113/	f	2026-07-16 17:26:16.633625+03	1
178	Yeni Personel Eklendi	hüsnü hüsnü sisteme yeni calisan olarak eklendi.	/envanter/calisanlar/114/	f	2026-07-16 17:29:34.787225+03	1
179	Cihaz Iadesi Alindi	Dell Sunucu X cihazinin iadesi basariyla alindi.	/envanter/cihazlarim/	f	2026-07-16 19:27:40.676606+03	9
180	Cihaz Iadesi Alindi	HP Sunucu 2024 cihazinin iadesi basariyla alindi.	/envanter/cihazlarim/	f	2026-07-17 09:26:27.859234+03	2
66	Yeni Zimmet Olusturuldu	HP Yazici Max cihazi uzerinize zimmetlendi.	/envanter/cihazlar/3/	f	2026-07-16 11:50:27.370451+03	10
\.


--
-- Name: accounts_user_groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.accounts_user_groups_id_seq', 1, false);


--
-- Name: accounts_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.accounts_user_id_seq', 42, true);


--
-- Name: accounts_user_user_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.accounts_user_user_permissions_id_seq', 1, false);


--
-- Name: auth_group_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auth_group_id_seq', 1, false);


--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auth_group_permissions_id_seq', 1, false);


--
-- Name: auth_permission_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auth_permission_id_seq', 64, true);


--
-- Name: django_admin_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.django_admin_log_id_seq', 25, true);


--
-- Name: django_content_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.django_content_type_id_seq', 16, true);


--
-- Name: django_migrations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.django_migrations_id_seq', 27, true);


--
-- Name: inventory_activitylog_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.inventory_activitylog_id_seq', 1136, true);


--
-- Name: inventory_assignment_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.inventory_assignment_id_seq', 213, true);


--
-- Name: inventory_company_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.inventory_company_id_seq', 28, true);


--
-- Name: inventory_device_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.inventory_device_id_seq', 188, true);


--
-- Name: inventory_employee_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.inventory_employee_id_seq', 114, true);


--
-- Name: inventory_notification_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.inventory_notification_id_seq', 180, true);


--
-- Name: accounts_user_groups accounts_user_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.accounts_user_groups
    ADD CONSTRAINT accounts_user_groups_pkey PRIMARY KEY (id);


--
-- Name: accounts_user_groups accounts_user_groups_user_id_group_id_59c0b32f_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.accounts_user_groups
    ADD CONSTRAINT accounts_user_groups_user_id_group_id_59c0b32f_uniq UNIQUE (user_id, group_id);


--
-- Name: accounts_user accounts_user_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.accounts_user
    ADD CONSTRAINT accounts_user_pkey PRIMARY KEY (id);


--
-- Name: accounts_user_user_permissions accounts_user_user_permi_user_id_permission_id_2ab516c2_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.accounts_user_user_permissions
    ADD CONSTRAINT accounts_user_user_permi_user_id_permission_id_2ab516c2_uniq UNIQUE (user_id, permission_id);


--
-- Name: accounts_user_user_permissions accounts_user_user_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.accounts_user_user_permissions
    ADD CONSTRAINT accounts_user_user_permissions_pkey PRIMARY KEY (id);


--
-- Name: accounts_user accounts_user_username_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.accounts_user
    ADD CONSTRAINT accounts_user_username_key UNIQUE (username);


--
-- Name: auth_group auth_group_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_group
    ADD CONSTRAINT auth_group_name_key UNIQUE (name);


--
-- Name: auth_group_permissions auth_group_permissions_group_id_permission_id_0cd325b0_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_group_id_permission_id_0cd325b0_uniq UNIQUE (group_id, permission_id);


--
-- Name: auth_group_permissions auth_group_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_pkey PRIMARY KEY (id);


--
-- Name: auth_group auth_group_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_group
    ADD CONSTRAINT auth_group_pkey PRIMARY KEY (id);


--
-- Name: auth_permission auth_permission_content_type_id_codename_01ab375a_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_content_type_id_codename_01ab375a_uniq UNIQUE (content_type_id, codename);


--
-- Name: auth_permission auth_permission_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_pkey PRIMARY KEY (id);


--
-- Name: django_admin_log django_admin_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_pkey PRIMARY KEY (id);


--
-- Name: django_content_type django_content_type_app_label_model_76bd3d3b_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_content_type
    ADD CONSTRAINT django_content_type_app_label_model_76bd3d3b_uniq UNIQUE (app_label, model);


--
-- Name: django_content_type django_content_type_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_content_type
    ADD CONSTRAINT django_content_type_pkey PRIMARY KEY (id);


--
-- Name: django_migrations django_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_migrations
    ADD CONSTRAINT django_migrations_pkey PRIMARY KEY (id);


--
-- Name: django_session django_session_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_session
    ADD CONSTRAINT django_session_pkey PRIMARY KEY (session_key);


--
-- Name: inventory_activitylog inventory_activitylog_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_activitylog
    ADD CONSTRAINT inventory_activitylog_pkey PRIMARY KEY (id);


--
-- Name: inventory_assignment inventory_assignment_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_assignment
    ADD CONSTRAINT inventory_assignment_pkey PRIMARY KEY (id);


--
-- Name: inventory_company inventory_company_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_company
    ADD CONSTRAINT inventory_company_name_key UNIQUE (name);


--
-- Name: inventory_company inventory_company_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_company
    ADD CONSTRAINT inventory_company_pkey PRIMARY KEY (id);


--
-- Name: inventory_device inventory_device_name_009b2458_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_device
    ADD CONSTRAINT inventory_device_name_009b2458_uniq UNIQUE (name);


--
-- Name: inventory_device inventory_device_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_device
    ADD CONSTRAINT inventory_device_pkey PRIMARY KEY (id);


--
-- Name: inventory_employee inventory_employee_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_employee
    ADD CONSTRAINT inventory_employee_email_key UNIQUE (email);


--
-- Name: inventory_employee inventory_employee_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_employee
    ADD CONSTRAINT inventory_employee_pkey PRIMARY KEY (id);


--
-- Name: inventory_employee inventory_employee_tc_kimlik_no_1dec2ad1_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_employee
    ADD CONSTRAINT inventory_employee_tc_kimlik_no_1dec2ad1_uniq UNIQUE (tc_kimlik_no);


--
-- Name: inventory_employee inventory_employee_user_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_employee
    ADD CONSTRAINT inventory_employee_user_id_key UNIQUE (user_id);


--
-- Name: inventory_notification inventory_notification_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_notification
    ADD CONSTRAINT inventory_notification_pkey PRIMARY KEY (id);


--
-- Name: accounts_user_groups_group_id_bd11a704; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX accounts_user_groups_group_id_bd11a704 ON public.accounts_user_groups USING btree (group_id);


--
-- Name: accounts_user_groups_user_id_52b62117; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX accounts_user_groups_user_id_52b62117 ON public.accounts_user_groups USING btree (user_id);


--
-- Name: accounts_user_user_permissions_permission_id_113bb443; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX accounts_user_user_permissions_permission_id_113bb443 ON public.accounts_user_user_permissions USING btree (permission_id);


--
-- Name: accounts_user_user_permissions_user_id_e4f0a161; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX accounts_user_user_permissions_user_id_e4f0a161 ON public.accounts_user_user_permissions USING btree (user_id);


--
-- Name: accounts_user_username_6088629e_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX accounts_user_username_6088629e_like ON public.accounts_user USING btree (username varchar_pattern_ops);


--
-- Name: auth_group_name_a6ea08ec_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX auth_group_name_a6ea08ec_like ON public.auth_group USING btree (name varchar_pattern_ops);


--
-- Name: auth_group_permissions_group_id_b120cbf9; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX auth_group_permissions_group_id_b120cbf9 ON public.auth_group_permissions USING btree (group_id);


--
-- Name: auth_group_permissions_permission_id_84c5c92e; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX auth_group_permissions_permission_id_84c5c92e ON public.auth_group_permissions USING btree (permission_id);


--
-- Name: auth_permission_content_type_id_2f476e4b; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX auth_permission_content_type_id_2f476e4b ON public.auth_permission USING btree (content_type_id);


--
-- Name: django_admin_log_content_type_id_c4bce8eb; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX django_admin_log_content_type_id_c4bce8eb ON public.django_admin_log USING btree (content_type_id);


--
-- Name: django_admin_log_user_id_c564eba6; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX django_admin_log_user_id_c564eba6 ON public.django_admin_log USING btree (user_id);


--
-- Name: django_session_expire_date_a5c62663; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX django_session_expire_date_a5c62663 ON public.django_session USING btree (expire_date);


--
-- Name: django_session_session_key_c0390e0f_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX django_session_session_key_c0390e0f_like ON public.django_session USING btree (session_key varchar_pattern_ops);


--
-- Name: inventory_a_created_fcdbcb_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX inventory_a_created_fcdbcb_idx ON public.inventory_activitylog USING btree (created_at DESC);


--
-- Name: inventory_activitylog_user_id_e4a6413e; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX inventory_activitylog_user_id_e4a6413e ON public.inventory_activitylog USING btree (user_id);


--
-- Name: inventory_assignment_assigned_by_id_65a9fc0e; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX inventory_assignment_assigned_by_id_65a9fc0e ON public.inventory_assignment USING btree (assigned_by_id);


--
-- Name: inventory_assignment_device_id_b776296b; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX inventory_assignment_device_id_b776296b ON public.inventory_assignment USING btree (device_id);


--
-- Name: inventory_assignment_employee_id_3a23febf; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX inventory_assignment_employee_id_3a23febf ON public.inventory_assignment USING btree (employee_id);


--
-- Name: inventory_assignment_returned_by_id_9ef8825a; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX inventory_assignment_returned_by_id_9ef8825a ON public.inventory_assignment USING btree (returned_by_id);


--
-- Name: inventory_company_name_ac2fdca8_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX inventory_company_name_ac2fdca8_like ON public.inventory_company USING btree (name varchar_pattern_ops);


--
-- Name: inventory_d_name_59f036_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX inventory_d_name_59f036_idx ON public.inventory_device USING btree (name);


--
-- Name: inventory_device_name_009b2458_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX inventory_device_name_009b2458_like ON public.inventory_device USING btree (name varchar_pattern_ops);


--
-- Name: inventory_employee_company_id_8bec41c0; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX inventory_employee_company_id_8bec41c0 ON public.inventory_employee USING btree (company_id);


--
-- Name: inventory_employee_email_d80fd5f6_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX inventory_employee_email_d80fd5f6_like ON public.inventory_employee USING btree (email varchar_pattern_ops);


--
-- Name: inventory_employee_tc_kimlik_no_1dec2ad1_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX inventory_employee_tc_kimlik_no_1dec2ad1_like ON public.inventory_employee USING btree (tc_kimlik_no varchar_pattern_ops);


--
-- Name: inventory_notification_user_id_b5616c82; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX inventory_notification_user_id_b5616c82 ON public.inventory_notification USING btree (user_id);


--
-- Name: accounts_user_groups accounts_user_groups_group_id_bd11a704_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.accounts_user_groups
    ADD CONSTRAINT accounts_user_groups_group_id_bd11a704_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES public.auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: accounts_user_groups accounts_user_groups_user_id_52b62117_fk_accounts_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.accounts_user_groups
    ADD CONSTRAINT accounts_user_groups_user_id_52b62117_fk_accounts_user_id FOREIGN KEY (user_id) REFERENCES public.accounts_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: accounts_user_user_permissions accounts_user_user_p_permission_id_113bb443_fk_auth_perm; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.accounts_user_user_permissions
    ADD CONSTRAINT accounts_user_user_p_permission_id_113bb443_fk_auth_perm FOREIGN KEY (permission_id) REFERENCES public.auth_permission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: accounts_user_user_permissions accounts_user_user_p_user_id_e4f0a161_fk_accounts_; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.accounts_user_user_permissions
    ADD CONSTRAINT accounts_user_user_p_user_id_e4f0a161_fk_accounts_ FOREIGN KEY (user_id) REFERENCES public.accounts_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_group_permissions auth_group_permissio_permission_id_84c5c92e_fk_auth_perm; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissio_permission_id_84c5c92e_fk_auth_perm FOREIGN KEY (permission_id) REFERENCES public.auth_permission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_group_permissions auth_group_permissions_group_id_b120cbf9_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_group_id_b120cbf9_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES public.auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_permission auth_permission_content_type_id_2f476e4b_fk_django_co; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_content_type_id_2f476e4b_fk_django_co FOREIGN KEY (content_type_id) REFERENCES public.django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_admin_log django_admin_log_content_type_id_c4bce8eb_fk_django_co; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_content_type_id_c4bce8eb_fk_django_co FOREIGN KEY (content_type_id) REFERENCES public.django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_admin_log django_admin_log_user_id_c564eba6_fk_accounts_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_user_id_c564eba6_fk_accounts_user_id FOREIGN KEY (user_id) REFERENCES public.accounts_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: inventory_activitylog inventory_activitylog_user_id_e4a6413e_fk_accounts_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_activitylog
    ADD CONSTRAINT inventory_activitylog_user_id_e4a6413e_fk_accounts_user_id FOREIGN KEY (user_id) REFERENCES public.accounts_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: inventory_assignment inventory_assignment_assigned_by_id_65a9fc0e_fk_accounts_; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_assignment
    ADD CONSTRAINT inventory_assignment_assigned_by_id_65a9fc0e_fk_accounts_ FOREIGN KEY (assigned_by_id) REFERENCES public.accounts_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: inventory_assignment inventory_assignment_device_id_b776296b_fk_inventory_device_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_assignment
    ADD CONSTRAINT inventory_assignment_device_id_b776296b_fk_inventory_device_id FOREIGN KEY (device_id) REFERENCES public.inventory_device(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: inventory_assignment inventory_assignment_employee_id_3a23febf_fk_inventory; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_assignment
    ADD CONSTRAINT inventory_assignment_employee_id_3a23febf_fk_inventory FOREIGN KEY (employee_id) REFERENCES public.inventory_employee(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: inventory_assignment inventory_assignment_returned_by_id_9ef8825a_fk_accounts_; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_assignment
    ADD CONSTRAINT inventory_assignment_returned_by_id_9ef8825a_fk_accounts_ FOREIGN KEY (returned_by_id) REFERENCES public.accounts_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: inventory_employee inventory_employee_company_id_8bec41c0_fk_inventory_company_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_employee
    ADD CONSTRAINT inventory_employee_company_id_8bec41c0_fk_inventory_company_id FOREIGN KEY (company_id) REFERENCES public.inventory_company(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: inventory_employee inventory_employee_user_id_df4f6208_fk_accounts_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_employee
    ADD CONSTRAINT inventory_employee_user_id_df4f6208_fk_accounts_user_id FOREIGN KEY (user_id) REFERENCES public.accounts_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: inventory_notification inventory_notification_user_id_b5616c82_fk_accounts_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_notification
    ADD CONSTRAINT inventory_notification_user_id_b5616c82_fk_accounts_user_id FOREIGN KEY (user_id) REFERENCES public.accounts_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- PostgreSQL database dump complete
--

\unrestrict qKTkG6mLcc8PEE83435dzUpaiXdfT6kAfDpxczuMSNDTK4iSPGXK8yEfq1hEN8C

