-- DermaNova Medical Platform - MySQL Schema
-- Fully aligned with app.py and SQLite schemas.
-- Database Name: `skin_cancer_db`

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

-- --------------------------------------------------------
-- Table Structure: `users`
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS `users` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `username` VARCHAR(50) UNIQUE NOT NULL,
  `email` VARCHAR(100) UNIQUE NOT NULL,
  `password` VARCHAR(255) NOT NULL,
  `full_name` VARCHAR(100) DEFAULT NULL,
  `role` VARCHAR(20) DEFAULT 'user',
  `avatar` VARCHAR(255) DEFAULT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_login` DATETIME DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------
-- Table Structure: `patients`
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS `patients` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL,
  `name` VARCHAR(100) NOT NULL,
  `age` INT DEFAULT NULL,
  `gender` VARCHAR(20) DEFAULT 'Autre',
  `result` VARCHAR(20) NOT NULL,
  `probability` FLOAT NOT NULL,
  `image_path` VARCHAR(255) NOT NULL,
  `notes` TEXT DEFAULT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------
-- Table Structure: `contacts`
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS `contacts` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(100) NOT NULL,
  `email` VARCHAR(100) NOT NULL,
  `subject` VARCHAR(150) DEFAULT NULL,
  `message` TEXT NOT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------
-- Seed Data for `users`
-- --------------------------------------------------------
-- Werkzeug secure scrypt hashes for 'Admin1234' and 'Doctor123'
INSERT INTO `users` (`id`, `username`, `email`, `password`, `full_name`, `role`) VALUES
(1, 'admin', 'admin@DermaNova.tn', 'scrypt:32768:8:1$uGLhLRykvECPgCOm$cc66325dacbe50bc27dbab2936f376387d7d9dcd4b83ef7bdf8f2a0ab5571ae676fab5fe2e759d27899b68534b83c0acbe2fc91b0a51031831305e6b9826f112', 'Administrateur DermaNova', 'admin'),
(2, 'dr_demo', 'demo@DermaNova.tn', 'scrypt:32768:8:1$8qpgRNBfsx5k3ENE$e338d20cf8ce748ae2d7ae28e6f606a201a77f3dda2295dd5fbb3943e5234123b7005cb4548dd59c0246bc1d36318a4c48c58f8668b8612b99b77cdd52581e0c', 'Dr. Demo Médecin', 'doctor')
ON DUPLICATE KEY UPDATE `id`=`id`;

COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
