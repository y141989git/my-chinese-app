import { sqliteTable, text, integer, primaryKey } from 'drizzle-orm/sqlite-core';
export const learningRecords = sqliteTable('learning_records', {
  userId: text('user_id').notNull(),
  recordKey: text('record_key').notNull(),
  value: text('value').notNull(),
  updatedAt: integer('updated_at').notNull(),
}, table => [primaryKey({columns:[table.userId,table.recordKey]})]);
