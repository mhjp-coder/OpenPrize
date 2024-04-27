CREATE TABLE settings (
  setting_name TEXT NOT NULL PRIMARY KEY,
  setting_value TEXT NOT NULL
);
INSERT INTO settings (setting_name, setting_value)
VALUES ('hx_remove_winner', 'off');
INSERT INTO settings (setting_name, setting_value)
VALUES ('hx_log_winner', 'off');
CREATE TABLE names (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  first_name TEXT NOT NULL,
  last_name TEXT NULL,
  organization TEXT NULL,
  email TEXT NULL
);
CREATE TABLE winners (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  first_name TEXT NOT NULL,
  last_name TEXT NULL,
  organization TEXT NULL,
  email TEXT NULL,
  prize INTEGER NULL,
  FOREIGN KEY(prize) REFERENCES prizes_won(rowid)
);
CREATE TABLE prizes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  prize TEXT NOT NULL,
  description TEXT NULL,
  sponsor TEXT NULL
);
CREATE TABLE prizes_won (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  prize TEXT NOT NULL,
  description TEXT NULL,
  sponsor TEXT NULL
);
