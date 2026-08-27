CREATE TABLE "passwordauth_credentials" (
    "user_id"         uuid PRIMARY KEY,
    "password_hash"   text NOT NULL,
    "failed_attempts" int  NOT NULL DEFAULT 0,
    "locked_until"    timestamptz NULL
);
