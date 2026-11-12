CREATE TABLE `learning_records` (
	`user_id` text NOT NULL,
	`record_key` text NOT NULL,
	`value` text NOT NULL,
	`updated_at` integer NOT NULL,
	PRIMARY KEY(`user_id`, `record_key`)
);
