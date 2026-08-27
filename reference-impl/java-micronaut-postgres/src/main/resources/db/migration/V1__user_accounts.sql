CREATE TABLE "user_accounts" (
    "user_id"   uuid PRIMARY KEY,
    "username"  varchar(255) NOT NULL UNIQUE
);
