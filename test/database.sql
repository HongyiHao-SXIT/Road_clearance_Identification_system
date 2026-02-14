-- TrashDet 初始化 SQL
-- 说明:
--  1) 本文件包含两个可选区段: MySQL 和 SQLite。请选择其中一个区段执行（不要同时执行两个）。
--  2) 若使用 MySQL: 运行 MySQL 客户端并执行 MySQL 区段（会创建数据库和表）。
--  3) 若使用 SQLite: 将 SQLite 区段保存为单独文件并用 `sqlite3` 导入，或直接执行下面的语句。
--  4) 本脚本包含示例数据，可根据需要注释或删除示例插入语句。

-- ====================
-- MySQL 初始化（如果你使用 MySQL / MariaDB）
-- ====================
-- 取消下面注释并在 MySQL 中执行（注意：会创建名为 `trashdet` 的数据库）
-- DROP DATABASE IF EXISTS `trashdet`;
-- CREATE DATABASE `trashdet` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
-- USE `trashdet`;

-- 用户表
CREATE TABLE IF NOT EXISTS `user` (
	`id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
	`username` VARCHAR(50) NOT NULL UNIQUE,
	`password_hash` VARCHAR(255) NOT NULL,
	`security_code` VARCHAR(255) NOT NULL,
	`role` VARCHAR(20) NOT NULL DEFAULT 'user'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 检测任务表
CREATE TABLE IF NOT EXISTS `detect_task` (
	`id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
	`source_type` VARCHAR(20),
	`source_path` VARCHAR(255),
	`result_path` VARCHAR(255),
	`device_id` VARCHAR(50),
	`location` VARCHAR(100),
	`status` VARCHAR(20) DEFAULT 'PENDING',
	`error_msg` TEXT,
	`created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
	`latitude` FLOAT,
	`longitude` FLOAT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 检测项表（关联 detect_task）
CREATE TABLE IF NOT EXISTS `detect_item` (
	`id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
	`task_id` INT,
	`label` VARCHAR(50),
	`confidence` FLOAT,
	`x1` INT,
	`y1` INT,
	`x2` INT,
	`y2` INT,
	`area` INT,
	`handle_state` VARCHAR(20) DEFAULT 'NEW',
	`updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	FOREIGN KEY (`task_id`) REFERENCES `detect_task`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 操作日志
CREATE TABLE IF NOT EXISTS `ops_log` (
	`id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
	`user_id` INT,
	`action` VARCHAR(255),
	`created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 机器人表
CREATE TABLE IF NOT EXISTS `robot` (
	`id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
	`device_id` VARCHAR(50) NOT NULL UNIQUE,
	`name` VARCHAR(100),
	`status` VARCHAR(20) DEFAULT 'OFFLINE',
	`ip_address` VARCHAR(50),
	`current_lat` FLOAT,
	`current_lng` FLOAT,
	`target_lat` FLOAT,
	`target_lng` FLOAT,
	`last_heartbeat` DATETIME DEFAULT CURRENT_TIMESTAMP,
	`next_command` VARCHAR(100) DEFAULT 'IDLE',
	`battery` INT DEFAULT 100,
	`config` TEXT DEFAULT '{"confidence_threshold": 0.5, "active": true}',
	`created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 示例数据（MySQL）
-- INSERT INTO `user` (username, password_hash, security_code, role) VALUES ('admin', '<password_hash_here>', '<security_code_here>', 'admin');
-- INSERT INTO `robot` (device_id, name, status, battery) VALUES ('SIM_ROBOT_001', 'Simulator', 'OFFLINE', 100);


-- ====================
-- SQLite 初始化（如果你使用 SQLite）
-- ====================
-- 如果使用 sqlite3，将下面区段复制到文件并执行：

-- PRAGMA foreign_keys = ON;

-- DROP TABLE IF EXISTS user;
CREATE TABLE IF NOT EXISTS user (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	username TEXT NOT NULL UNIQUE,
	password_hash TEXT NOT NULL,
	security_code TEXT NOT NULL,
	role TEXT NOT NULL DEFAULT 'user'
);

-- drop and create detect_task
DROP TABLE IF EXISTS detect_task;
CREATE TABLE IF NOT EXISTS detect_task (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	source_type TEXT,
	source_path TEXT,
	result_path TEXT,
	device_id TEXT,
	location TEXT,
	status TEXT DEFAULT 'PENDING',
	error_msg TEXT,
	created_at DATETIME DEFAULT (datetime('now')),
	latitude REAL,
	longitude REAL
);

DROP TABLE IF EXISTS detect_item;
CREATE TABLE IF NOT EXISTS detect_item (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	task_id INTEGER,
	label TEXT,
	confidence REAL,
	x1 INTEGER,
	y1 INTEGER,
	x2 INTEGER,
	y2 INTEGER,
	area INTEGER,
	handle_state TEXT DEFAULT 'NEW',
	updated_at DATETIME DEFAULT (datetime('now')),
	FOREIGN KEY(task_id) REFERENCES detect_task(id) ON DELETE CASCADE
);

DROP TABLE IF EXISTS ops_log;
CREATE TABLE IF NOT EXISTS ops_log (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	user_id INTEGER,
	action TEXT,
	created_at DATETIME DEFAULT (datetime('now'))
);

DROP TABLE IF EXISTS robot;
CREATE TABLE IF NOT EXISTS robot (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	device_id TEXT NOT NULL UNIQUE,
	name TEXT,
	status TEXT DEFAULT 'OFFLINE',
	ip_address TEXT,
	current_lat REAL,
	current_lng REAL,
	target_lat REAL,
	target_lng REAL,
	last_heartbeat DATETIME DEFAULT (datetime('now')),
	next_command TEXT DEFAULT 'IDLE',
	battery INTEGER DEFAULT 100,
	config TEXT DEFAULT '{"confidence_threshold": 0.5, "active": true}',
	created_at DATETIME DEFAULT (datetime('now'))
);

-- 示例数据（SQLite）
-- INSERT INTO user (username, password_hash, security_code, role) VALUES ('admin', '<password_hash_here>', '<security_code_here>', 'admin');
-- INSERT INTO robot (device_id, name, status, battery) VALUES ('SIM_ROBOT_001', 'Simulator', 'OFFLINE', 100);

-- ====================
-- 使用示例：
-- MySQL:  mysql -u root -p < test/database.sql   (先去掉 SQLite 段或执行 MySQL 段)
-- SQLite: sqlite3 trashdet.db < test/database.sql  (先只保留 SQLite 段或复制对应语句)
-- 注意：密码哈希与安全码请使用应用中的工具/脚本生成并替换示例值。