#!/bin/bash
# Runs inside a one-shot init container after MongoDB is healthy.
# 1. Initiates the single-node replica set (required for change streams / SSE).
# 2. Waits for the primary to be elected.
# 3. Creates indexes on the main database (idempotent — safe to re-run).

set -e

echo "[mongo-init] Initiating replica set rs0..."
mongosh --host mongodb:27017 --quiet --eval '
  try {
    rs.initiate({ _id: "rs0", members: [{ _id: 0, host: "mongodb:27017" }] });
    print("[mongo-init] Replica set initiated.");
  } catch (e) {
    if (e.codeName === "AlreadyInitialized") {
      print("[mongo-init] Replica set already initiated — skipping.");
    } else {
      throw e;
    }
  }
'

echo "[mongo-init] Waiting for primary election..."
until mongosh --host mongodb:27017 --quiet --eval 'rs.status().myState' 2>/dev/null | grep -q "^1$"; do
  echo "[mongo-init] Not primary yet, retrying in 2s..."
  sleep 2
done
echo "[mongo-init] Primary elected."

echo "[mongo-init] Creating indexes on database 'main'..."
mongosh --host mongodb:27017 --quiet --eval '
  const db = db.getSiblingDB("main");

  // sessions — looked up by session_id (unique) and filtered by status
  db.sessions.createIndex({ session_id: 1 }, { unique: true, name: "sessions_by_id" });
  db.sessions.createIndex({ status: 1 },     { name: "sessions_by_status" });

  // chats — fetched by session + time order; filtered by archived flag
  db.chats.createIndex({ session_id: 1, message_time_usec: 1 }, { name: "chats_by_session_time" });
  db.chats.createIndex({ session_id: 1, is_archived: 1 },       { name: "chats_by_session_archive" });

  // info — looked up by video_id
  db.info.createIndex({ video_id: 1 }, { name: "info_by_video_id" });

  print("[mongo-init] Indexes ready:");
  db.sessions.getIndexes().forEach(i => print("  sessions: " + i.name));
  db.chats.getIndexes().forEach(i   => print("  chats: "    + i.name));
  db.info.getIndexes().forEach(i    => print("  info: "     + i.name));
  print("[mongo-init] Done.");
'
