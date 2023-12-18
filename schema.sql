CREATE TABLE naan (
  naan INTEGER PRIMARY KEY,
  name TEXT,
  description TEXT,
  url TEXT
);

CREATE TABLE shoulder (
  shoulder TEXT PRIMARY KEY,
  naan INTEGER,
  name TEXT,
  description TEXT,
  FOREIGN KEY(naan) REFERENCES naan(naan)
);

CREATE TABLE ark (
  identifier TEXT PRIMARY KEY,
  naan INTEGER,
  assigned_name TEXT,
  shoulder TEXT,
  url TEXT,
  meta TEXT,
  FOREIGN KEY (naan) REFERENCES naan(naan),
  FOREIGN KEY (shoulder) REFERENCES shoulder(shoulder)
);

CREATE INDEX idx_assigned_name ON ark(assigned_name);


