-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Jun 14, 2025 at 08:46 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.0.30

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `creditbank`
--
CREATE DATABASE IF NOT EXISTS `creditbank` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `creditbank`;

-- --------------------------------------------------------

--
-- Table structure for table `admin`
--

CREATE TABLE `admin` (
  `id` int(11) NOT NULL,
  `first_name` varchar(255) NOT NULL,
  `last_name` varchar(255) NOT NULL,
  `email` varchar(100) NOT NULL,
  `username` varchar(10) NOT NULL,
  `gender` enum('Male','Female') NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` enum('admin') NOT NULL,
  `tel` varchar(20) NOT NULL,
  `profile_image` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `admin`
--

INSERT INTO `admin` (`id`, `first_name`, `last_name`, `email`, `username`, `gender`, `password`, `role`, `tel`, `profile_image`) VALUES
(3, 'admin', 'teste', 'admin@gmail.com', 'admin', 'Male', 'scrypt:32768:8:1$vkJUSWAzx0Vsmj98$0ca7495f5c23fb3065e2258f3087160b9dfb8167b0596a3ba664f7dd4f87953e799eada96e4022b91232aac0cba897fa05c4644da9f826d63a3879cce47f0d8d', 'admin', '0987676774', NULL),
(7, 'supap', 'rukdee', 'asdadasd@gmail.com', 'tests1234', 'Male', 'scrypt:32768:8:1$twRmfoNf9zTyjogk$30ba73f74e0b685b6ba47cc895c1b8c12b80a97b6ac6cb94b8e212600f39e9340c3e3b6055b9e3d2904995ac73a4c869bb3e4b94e20fdf6c833bd0dfef6c3b57', 'admin', '0944334455', NULL);

-- --------------------------------------------------------

--
-- Table structure for table `categories`
--

CREATE TABLE `categories` (
  `id` int(11) NOT NULL,
  `name` varchar(200) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `categories`
--

INSERT INTO `categories` (`id`, `name`) VALUES
(0, 'cybersecurity');

-- --------------------------------------------------------

--
-- Table structure for table `courses`
--

CREATE TABLE `courses` (
  `id` int(11) NOT NULL,
  `featured_image` varchar(255) DEFAULT NULL,
  `title` varchar(255) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `instructor_id` int(11) NOT NULL,
  `categories_id` int(11) NOT NULL,
  `description` text DEFAULT NULL,
  `status` enum('publish','draft') NOT NULL DEFAULT 'draft',
  `featured_video` varchar(300) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `courses`
--

INSERT INTO `courses` (`id`, `featured_image`, `title`, `created_at`, `instructor_id`, `categories_id`, `description`, `status`, `featured_video`) VALUES
(9, 'testy.jpg', 'test', '2025-06-10 18:00:18', 6, 0, 'Desty', 'publish', NULL);

-- --------------------------------------------------------

--
-- Table structure for table `instructor`
--

CREATE TABLE `instructor` (
  `id` int(11) NOT NULL,
  `first_name` varchar(255) NOT NULL,
  `last_name` varchar(255) NOT NULL,
  `email` varchar(100) NOT NULL,
  `username` varchar(10) NOT NULL,
  `gender` enum('Male','Female') NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` enum('instructor') NOT NULL,
  `tel` varchar(20) NOT NULL,
  `profile_image` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `instructor`
--

INSERT INTO `instructor` (`id`, `first_name`, `last_name`, `email`, `username`, `gender`, `password`, `role`, `tel`, `profile_image`) VALUES
(6, 'jamjann', 'mungpijit', 'instructor@gmail.com', 'instructor', 'Female', 'scrypt:32768:8:1$zBTKTEERcHaUHLtz$138f13bcafffe559ac5c294ffa493f010e93b3294351e8b48ee76910a2f58afc555df4ae45e2dc50ae9ee7b69e5fecb8cb79c3b590d4708e65ad93572a9d7ffc', 'instructor', '0944334433', NULL),
(7, 'lao', 'ty', 'twfsdfdd@gmail.com', 'test2', 'Female', 'scrypt:32768:8:1$BJZDSC4sBWip9fRo$6065696a9106fc04616baade252d53717f96e929c9f56ffa94db76af067ff61309426bc823cf653b25297cf689654df05079bada812502ab2531efa2150fca6b', 'instructor', '0944334778', NULL);

-- --------------------------------------------------------

--
-- Table structure for table `lesson`
--

CREATE TABLE `lesson` (
  `lesson_id` int(11) NOT NULL,
  `lesson_name` varchar(255) NOT NULL,
  `lesson_date` datetime NOT NULL,
  `course_id` int(11) NOT NULL,
  `instructor_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `lesson`
--

INSERT INTO `lesson` (`lesson_id`, `lesson_name`, `lesson_date`, `course_id`, `instructor_id`) VALUES
(0, 'test', '2025-06-11 16:29:52', 9, 6);

-- --------------------------------------------------------

--
-- Table structure for table `questions`
--

CREATE TABLE `questions` (
  `question_id` int(11) NOT NULL,
  `quiz_id` int(11) NOT NULL,
  `score` int(11) NOT NULL,
  `question_name` varchar(255) NOT NULL,
  `choice_a` varchar(255) NOT NULL,
  `choice_b` varchar(255) NOT NULL,
  `choice_c` varchar(255) NOT NULL,
  `choice_d` varchar(255) NOT NULL,
  `correct_answer` enum('a','b','c','d') NOT NULL,
  `question_image` varchar(255) NOT NULL,
  `choice_a_image` varchar(255) NOT NULL,
  `choice_b_image` varchar(255) NOT NULL,
  `choice_c_image` varchar(255) NOT NULL,
  `choice_d_image` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `questions`
--

INSERT INTO `questions` (`question_id`, `quiz_id`, `score`, `question_name`, `choice_a`, `choice_b`, `choice_c`, `choice_d`, `correct_answer`, `question_image`, `choice_a_image`, `choice_b_image`, `choice_c_image`, `choice_d_image`) VALUES
(1, 3, 1, 'test', 'a', 'b', 'c', 'd', 'a', '', '', '', '', ''),
(2, 4, 1, 'tesr', 'a', 'b', 'c', 'd', 'a', '', '', '', '', ''),
(8, 4, 1, 'เไะเไพเไเ', 'นั้นสิ', 'b', 'เไำเำไ', 'โอเค', 'a', 'testy.jpg', 'logo.png', 'testy.jpg', 'logo.png', 'testy.jpg');

-- --------------------------------------------------------

--
-- Table structure for table `quiz`
--

CREATE TABLE `quiz` (
  `quiz_id` int(11) NOT NULL,
  `quiz_name` varchar(100) NOT NULL,
  `lesson_id` int(11) NOT NULL,
  `passing_percentage` int(11) NOT NULL,
  `quiz_date` datetime NOT NULL,
  `quiz_type` enum('Pre-test','Post_test','','') NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `quiz`
--

INSERT INTO `quiz` (`quiz_id`, `quiz_name`, `lesson_id`, `passing_percentage`, `quiz_date`, `quiz_type`) VALUES
(1, 'secur', 0, 50, '2025-06-12 20:26:00', 'Pre-test'),
(3, 'secur', 0, 40, '2025-06-14 17:05:37', 'Pre-test'),
(4, 'rerew', 0, 40, '2025-06-14 17:47:01', 'Pre-test');

-- --------------------------------------------------------

--
-- Table structure for table `user`
--

CREATE TABLE `user` (
  `id` int(11) NOT NULL,
  `first_name` varchar(100) NOT NULL,
  `last_name` varchar(100) NOT NULL,
  `email` varchar(255) NOT NULL,
  `username` varchar(100) NOT NULL,
  `id_card` varchar(13) NOT NULL,
  `gender` enum('male','female','other') NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` enum('user') NOT NULL DEFAULT 'user',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `profile_image` varchar(255) NOT NULL DEFAULT 'default.jpg',
  `tel` varchar(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `user`
--

INSERT INTO `user` (`id`, `first_name`, `last_name`, `email`, `username`, `id_card`, `gender`, `password`, `role`, `created_at`, `profile_image`, `tel`) VALUES
(34, 'ubann', 'titu', 'qwer@gmail.com', 'user', '7777777754545', 'male', 'scrypt:32768:8:1$NUevnNNTHXSBUFvB$74d34d9e28b8030da208d104ba294a9c8e4c538b0385f874dcb2408e5eb49ce944735c159b00df4bd2a902b0289bb571a2fbbc37c6b57f82bf6029a6435bd253', 'user', '2025-06-09 09:41:39', 'default.jpg', '0987676789');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `admin`
--
ALTER TABLE `admin`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `categories`
--
ALTER TABLE `categories`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `courses`
--
ALTER TABLE `courses`
  ADD PRIMARY KEY (`id`),
  ADD KEY `instructor_id` (`instructor_id`),
  ADD KEY `categories_id` (`categories_id`);

--
-- Indexes for table `instructor`
--
ALTER TABLE `instructor`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `lesson`
--
ALTER TABLE `lesson`
  ADD PRIMARY KEY (`lesson_id`);

--
-- Indexes for table `questions`
--
ALTER TABLE `questions`
  ADD PRIMARY KEY (`question_id`),
  ADD KEY `fk_quiz` (`quiz_id`);

--
-- Indexes for table `quiz`
--
ALTER TABLE `quiz`
  ADD PRIMARY KEY (`quiz_id`),
  ADD KEY `fk_quiz_lesson` (`lesson_id`);

--
-- Indexes for table `user`
--
ALTER TABLE `user`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`),
  ADD UNIQUE KEY `username` (`username`),
  ADD UNIQUE KEY `id_card` (`id_card`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `admin`
--
ALTER TABLE `admin`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT for table `courses`
--
ALTER TABLE `courses`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=10;

--
-- AUTO_INCREMENT for table `instructor`
--
ALTER TABLE `instructor`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT for table `questions`
--
ALTER TABLE `questions`
  MODIFY `question_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- AUTO_INCREMENT for table `quiz`
--
ALTER TABLE `quiz`
  MODIFY `quiz_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `user`
--
ALTER TABLE `user`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=36;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `courses`
--
ALTER TABLE `courses`
  ADD CONSTRAINT `courses_ibfk_1` FOREIGN KEY (`instructor_id`) REFERENCES `instructor` (`id`),
  ADD CONSTRAINT `courses_ibfk_2` FOREIGN KEY (`categories_id`) REFERENCES `categories` (`id`);

--
-- Constraints for table `questions`
--
ALTER TABLE `questions`
  ADD CONSTRAINT `fk_quiz` FOREIGN KEY (`quiz_id`) REFERENCES `quiz` (`quiz_id`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `quiz`
--
ALTER TABLE `quiz`
  ADD CONSTRAINT `fk_quiz_lesson` FOREIGN KEY (`lesson_id`) REFERENCES `lesson` (`lesson_id`) ON DELETE CASCADE ON UPDATE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
