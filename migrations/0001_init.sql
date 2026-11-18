-- Owner database, schema version 1 (docs/DATABASE.md section 2).
-- Names and last-4 Aadhaar are encrypted by the application (Fernet); masked PAN is not secret.

CREATE TABLE owner (
    id                  INTEGER PRIMARY KEY,
    owner_name_enc      BLOB    NOT NULL,
    pan_masked          TEXT    CHECK (pan_masked IS NULL OR (length(pan_masked) = 10 AND substr(pan_masked, 6, 4) = '****')),
    aadhaar_last4_enc   BLOB,
    owner_source        TEXT    NOT NULL CHECK (length(owner_source) > 0),
    verified_on         TEXT    NOT NULL,
    created_at          TEXT    NOT NULL,
    updated_at          TEXT    NOT NULL
);

CREATE TABLE owner_parcel (
    id          INTEGER PRIMARY KEY,
    owner_id    INTEGER NOT NULL REFERENCES owner(id) ON DELETE RESTRICT,
    district    TEXT    NOT NULL,
    taluk       TEXT    NOT NULL,
    village     TEXT    NOT NULL,
    survey_no   TEXT    NOT NULL,
    parcel_ref  TEXT,
    linked_on   TEXT    NOT NULL,
    UNIQUE (owner_id, district, taluk, village, survey_no)
);

CREATE TABLE owner_access_log (
    id          INTEGER PRIMARY KEY,
    owner_id    INTEGER NOT NULL REFERENCES owner(id) ON DELETE RESTRICT,
    action      TEXT    NOT NULL CHECK (action IN ('view', 'create', 'update', 'delete')),
    at          TEXT    NOT NULL,
    session_ref TEXT
);

CREATE INDEX idx_owner_parcel_location ON owner_parcel (district, taluk, village, survey_no);
CREATE INDEX idx_owner_parcel_owner    ON owner_parcel (owner_id);
CREATE INDEX idx_access_owner_at       ON owner_access_log (owner_id, at);
