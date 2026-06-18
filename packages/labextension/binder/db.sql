PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE alembic_version (
	version_num VARCHAR(32) NOT NULL,
	CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);
INSERT INTO alembic_version VALUES('a0718dae969d');
CREATE TABLE lecture (
	id INTEGER NOT NULL,
	name VARCHAR(255),
	code VARCHAR(255),
	state VARCHAR(8) NOT NULL,
	deleted VARCHAR(7) DEFAULT 'active' NOT NULL,
	created_at DATETIME NOT NULL,
	updated_at DATETIME NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (code)
);
INSERT INTO lecture VALUES(1,'lect1','lect1','active','active','2024-11-04 13:11:45.883175','2024-11-04 13:11:45.883180');
CREATE TABLE assignment (
	id INTEGER NOT NULL,
	name VARCHAR(255) NOT NULL,
	type VARCHAR(5) DEFAULT 'user' NOT NULL,
	lectid INTEGER,
	duedate DATETIME,
	automatic_grading VARCHAR(10) DEFAULT 'unassisted' NOT NULL,
	points DECIMAL(10, 3) NOT NULL,
	status VARCHAR(8),
	deleted VARCHAR(7) DEFAULT 'active' NOT NULL,
	max_submissions INTEGER,
	allow_files BOOLEAN NOT NULL,
	properties TEXT,
	created_at DATETIME NOT NULL,
	updated_at DATETIME NOT NULL, settings TEXT DEFAULT '{}' NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(lectid) REFERENCES lecture (id),
	CONSTRAINT u_name_in_lect UNIQUE (name, lectid, deleted)
);
CREATE TABLE takepart (
	user_id INTEGER NOT NULL,
	lectid INTEGER NOT NULL,
	role VARCHAR(255) NOT NULL,
	PRIMARY KEY (user_id, lectid),
	FOREIGN KEY(lectid) REFERENCES lecture (id),
	FOREIGN KEY(user_id) REFERENCES user (id)
);
INSERT INTO takepart VALUES(1,1,'instructor');
INSERT INTO takepart VALUES(2,1,'instructor');
INSERT INTO takepart VALUES(3,1,'student');

CREATE TABLE submission (
	id INTEGER NOT NULL,
	date DATETIME,
	auto_status VARCHAR(20) NOT NULL,
	manual_status VARCHAR(15) NOT NULL,
	edited BOOLEAN,
	score DECIMAL(10, 3),
	assignid INTEGER NOT NULL,
	user_id INTEGER NOT NULL,
	commit_hash VARCHAR(40) NOT NULL,
	updated_at DATETIME NOT NULL,
    grading_score DECIMAL(10, 3),
    score_scaling DECIMAL(10, 3) DEFAULT '1.0' NOT NULL,
    feedback_status VARCHAR(17) DEFAULT 'not_generated' NOT NULL,
    deleted VARCHAR(7) DEFAULT 'active' NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(assignid) REFERENCES assignment (id),
	FOREIGN KEY(user_id) REFERENCES user (id)
);
CREATE TABLE submission_logs (
	sub_id INTEGER NOT NULL,
	logs TEXT,
	PRIMARY KEY (sub_id),
	FOREIGN KEY(sub_id) REFERENCES submission (id)
);
CREATE TABLE submission_properties (
	sub_id INTEGER NOT NULL,
	properties TEXT,
	PRIMARY KEY (sub_id),
	FOREIGN KEY(sub_id) REFERENCES submission (id)
);
CREATE TABLE api_token (
	user_id INTEGER NOT NULL,
	id INTEGER,
	hashed VARCHAR(255),
	prefix VARCHAR(16),
	client_id VARCHAR(255),
	session_id VARCHAR(255),
	created DATETIME,
	expires_at DATETIME,
	last_activity DATETIME,
	note VARCHAR(1023),
	scopes TEXT,
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES user (id)
);
INSERT INTO api_token VALUES(1,1,'sha512:1:e1256354cdcaa527:2ff86945adeccfe0d7e145f3309ab2bdbe3ebade042040a66fd59c71653d5e0e86137a46a3669c83747b5c30da514a4cc390f9552705c0186b4154f42e078cc8','EFlj','hub','4518493cdf7944589e435d42c739ea7f','2024-11-04 13:12:05.114740','2024-11-18 13:12:05.113774','2024-11-04 13:12:05.126583','','["identify"]');
CREATE TABLE oauth_client (
	id INTEGER,
	identifier VARCHAR(255),
	description VARCHAR(1023),
	secret VARCHAR(255),
	redirect_uri VARCHAR(1023),
	allowed_scopes TEXT,
	PRIMARY KEY (id),
	UNIQUE (identifier)
);
INSERT INTO oauth_client VALUES(1,'hub','hub','sha512:16384:f0aa7f9c0c4a8803:cb18a221118c0358afa76cbb194189d2a01f0df1ab3f280c4dab96d1bb841282da14a47fd215741ec1c1c24cf843a647a7d248adeb1239acf549a23fce68bb24','http://localhost:8080/hub/oauth_callback',NULL);
CREATE TABLE oauth_code (
	id INTEGER,
	client_id VARCHAR(255),
	code VARCHAR(36),
	expires_at INTEGER,
	redirect_uri VARCHAR(1023),
	session_id VARCHAR(255),
	user_id INTEGER,
	scopes TEXT,
	PRIMARY KEY (id),
	FOREIGN KEY(client_id) REFERENCES oauth_client (identifier),
	FOREIGN KEY(user_id) REFERENCES user (id)
);
CREATE TABLE IF NOT EXISTS "user" (
    id INTEGER NOT NULL,
	name VARCHAR(255) NOT NULL,
	encrypted_auth_state BLOB,
	cookie_id VARCHAR(255) NOT NULL,
	PRIMARY KEY (id),
    UNIQUE (name),
	CONSTRAINT uq_user_cookie UNIQUE (cookie_id)
);
INSERT INTO user VALUES('admin',NULL,'0eead4756d8a4e9f8af65949b1d8bdd4');
INSERT INTO user VALUES('instructor',NULL,'0eead4756d8a4e9f8af65949b1d8bdd5');
INSERT INTO user VALUES('student',NULL,'0eead4756d8a4e9f8af65949b1d8bdd6');
COMMIT;
