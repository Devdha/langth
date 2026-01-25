import { openDB, DBSchema, IDBPDatabase } from 'idb';
import { TherapySession, GameSettingsV2 } from '@/types/v2';

const DB_NAME = 'talk-talk-v2';
const DB_VERSION = 1;
const STORE_NAME = 'sessions';

interface TalkTalkDB extends DBSchema {
  sessions: {
    key: string;
    value: TherapySession;
    indexes: {
      'by-updated': number;
      'by-created': number;
    };
  };
}

let dbPromise: Promise<IDBPDatabase<TalkTalkDB>> | null = null;

function getDB(): Promise<IDBPDatabase<TalkTalkDB>> {
  if (!dbPromise) {
    dbPromise = openDB<TalkTalkDB>(DB_NAME, DB_VERSION, {
      upgrade(db) {
        const store = db.createObjectStore(STORE_NAME, { keyPath: 'id' });
        store.createIndex('by-updated', 'updatedAt');
        store.createIndex('by-created', 'createdAt');
      },
    });
  }
  return dbPromise;
}

export function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

export async function createSession(
  name: string,
  settings: GameSettingsV2,
  metadata?: TherapySession['metadata']
): Promise<TherapySession> {
  const db = await getDB();
  const now = Date.now();

  const session: TherapySession = {
    id: generateId(),
    name,
    createdAt: now,
    updatedAt: now,
    settings,
    items: [],
    metadata: metadata || {},
  };

  await db.put(STORE_NAME, session);
  return session;
}

export async function getSession(id: string): Promise<TherapySession | undefined> {
  const db = await getDB();
  return db.get(STORE_NAME, id);
}

export async function getAllSessions(): Promise<TherapySession[]> {
  const db = await getDB();
  const sessions = await db.getAllFromIndex(STORE_NAME, 'by-updated');
  return sessions.reverse(); // Most recent first
}

export async function updateSession(
  id: string,
  updates: Partial<Omit<TherapySession, 'id' | 'createdAt'>>
): Promise<TherapySession | undefined> {
  const db = await getDB();
  const session = await db.get(STORE_NAME, id);

  if (!session) return undefined;

  const updated: TherapySession = {
    ...session,
    ...updates,
    updatedAt: Date.now(),
  };

  await db.put(STORE_NAME, updated);
  return updated;
}

export async function deleteSession(id: string): Promise<void> {
  const db = await getDB();
  await db.delete(STORE_NAME, id);
}

export async function duplicateSession(id: string): Promise<TherapySession | undefined> {
  const db = await getDB();
  const original = await db.get(STORE_NAME, id);

  if (!original) return undefined;

  const now = Date.now();
  const duplicated: TherapySession = {
    ...original,
    id: generateId(),
    name: `${original.name} (복사본)`,
    createdAt: now,
    updatedAt: now,
  };

  await db.put(STORE_NAME, duplicated);
  return duplicated;
}

export async function searchSessions(query: string): Promise<TherapySession[]> {
  const sessions = await getAllSessions();
  const lowerQuery = query.toLowerCase();

  return sessions.filter(session =>
    session.name.toLowerCase().includes(lowerQuery) ||
    session.metadata.patientName?.toLowerCase().includes(lowerQuery) ||
    session.metadata.notes?.toLowerCase().includes(lowerQuery)
  );
}

export async function getRecentSessions(limit: number = 5): Promise<TherapySession[]> {
  const sessions = await getAllSessions();
  return sessions.slice(0, limit);
}
