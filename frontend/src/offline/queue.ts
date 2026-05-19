import axios from "axios";
import { openDB } from "idb";
import type { FeedbackPayload } from "../api/feedback";
import { submitFeedback } from "../api/feedback";

const DB_NAME = "soite-offline";
const STORE = "feedback-queue";
const DB_VERSION = 1;

async function getDb() {
  return openDB(DB_NAME, DB_VERSION, {
    upgrade(db) {
      if (!db.objectStoreNames.contains(STORE)) {
        db.createObjectStore(STORE, { keyPath: "submission_id" });
      }
    },
  });
}

export async function enqueue(payload: FeedbackPayload): Promise<void> {
  const db = await getDb();
  await db.put(STORE, payload);
}

export async function drainQueue(): Promise<void> {
  const db = await getDb();
  const all = await db.getAll(STORE);
  for (const payload of all) {
    try {
      await submitFeedback(payload);
      await db.delete(STORE, payload.submission_id);
    } catch (err) {
      if (axios.isAxiosError(err) && err.response) {
        const status = err.response.status;
        if (status >= 400 && status < 500 && status !== 429) {
          // Permanent client error (malformed payload) — remove and continue
          await db.delete(STORE, payload.submission_id);
          continue;
        }
      }
      // Network error, 429, or 5xx — transient, stop and retry on next reconnect
      break;
    }
  }
}

export async function getQueueLength(): Promise<number> {
  const db = await getDb();
  return db.count(STORE);
}
