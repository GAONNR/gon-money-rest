CREATE TABLE table1 (id integer primary key);
CREATE TABLE user (
	no INTEGER NOT NULL, 
	uid VARCHAR(40) NOT NULL, 
	name VARCHAR(80), 
	nick VARCHAR(80) NOT NULL, 
	account VARCHAR(80), 
	profile_image VARCHAR(160), 
	reduce_money BOOLEAN, 
	confirm BOOLEAN, 
	notice BOOLEAN, 
	PRIMARY KEY (no), 
	UNIQUE (uid), 
	CHECK (reduce_money IN (0, 1)), 
	CHECK (confirm IN (0, 1)), 
	CHECK (notice IN (0, 1))
);
CREATE TABLE trade (
	no INTEGER NOT NULL, 
	eul_uid VARCHAR(40), 
	gab_uid VARCHAR(40), 
	price INTEGER NOT NULL, 
	reduce_price INTEGER, 
	date DATETIME, 
	content VARCHAR(160), 
	account VARCHAR(80), 
	completed BOOLEAN, 
	reduced BOOLEAN, 
	confirmed BOOLEAN, 
	PRIMARY KEY (no), 
	FOREIGN KEY(eul_uid) REFERENCES user (uid), 
	FOREIGN KEY(gab_uid) REFERENCES user (uid), 
	CHECK (completed IN (0, 1)), 
	CHECK (reduced IN (0, 1)), 
	CHECK (confirmed IN (0, 1))
);
