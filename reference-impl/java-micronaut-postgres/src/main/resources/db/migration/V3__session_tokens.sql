CREATE TABLE "session_tokens" (
    "session_token" uuid PRIMARY KEY,
    "user_id"       uuid NOT NULL
);
